"""
Ray Serve deployment demonstrating production-style, autoscaled model
serving across the multi-node Ray cluster (ray-head + 2 workers).

Run inside the ray-head container (see ray-cluster/README.md):

    docker compose exec ray-head python /home/ray/app/serve_app.py

The deployment autoscales its replica count based on load - exactly the
"scaling" behavior the JD calls out, and observable live in real time via
the Ray dashboard (http://localhost:8265) and the Grafana dashboards in
../monitoring while load_test.py is running against it.
"""
import time

import torch
import torch.nn as nn
from ray import serve


class TinyModel(nn.Module):
    """Stand-in for a real trained checkpoint (e.g. the DDP job's output)."""

    def __init__(self, dim: int = 1024):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.ReLU(),
            nn.Linear(dim, 10),
        )

    def forward(self, x):
        return self.net(x)


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 4,
        "target_ongoing_requests": 5,
        "upscale_delay_s": 5,
        "downscale_delay_s": 30,
    },
    ray_actor_options={"num_cpus": 1},
)
class ModelServer:
    def __init__(self):
        torch.manual_seed(0)
        self.model = TinyModel()
        self.model.eval()

    async def __call__(self, request):
        start = time.perf_counter()

        # Real inference: a random input tensor stands in for a decoded
        # request payload (e.g. tokenized text or preprocessed image).
        x = torch.randn(1, 1024)
        with torch.no_grad():
            logits = self.model(x)
        prediction = int(torch.argmax(logits, dim=-1).item())

        latency_ms = (time.perf_counter() - start) * 1000
        return {"prediction": prediction, "latency_ms": round(latency_ms, 3)}


app = ModelServer.bind()

if __name__ == "__main__":
    # http_options host="0.0.0.0" matters here: Ray Serve's HTTP proxy binds
    # 127.0.0.1 by default, which silently accepts-then-drops connections
    # that arrive via Docker's port mapping (they aren't from the
    # container's own loopback). Must be set via serve.start() before the
    # first serve.run() call - serve.run() itself takes no host/port args.
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    serve.run(app, name="model-server", route_prefix="/predict")
    print("Ray Serve deployment 'model-server' is live at http://ray-head:8000/predict")
    print("Autoscaling: min_replicas=1, max_replicas=4 (see autoscaling_config above)")
    # Keep the process alive so the deployment stays up; Ctrl+C to stop.
    while True:
        time.sleep(3600)
