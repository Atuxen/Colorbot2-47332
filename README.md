# 47332 AI-orchestrated self-driving labs

This repository contains the exercises for the course 47332 AI-orchestrated self-driving labs, 2025

## Running in Jupyterlab in Docker (Recommended)

### 1. Install Docker Desktop

Download and install Docker Desktop from:  
https://www.docker.com/products/docker-desktop/

Make sure it's running before you continue.

---

### 2. Clone This Repository

In your terminal:

```bash
git clone https://github.com/Atuxen/Colorbot2-47332.git
cd Colorbot2-47332
docker compose up --build
```

This should let you open http://localhost:8888/ in your browser where all dependencies are now installed.

Next time you only need to: 
```bash
docker compose up
```
---

# Alternatively: Running locally in venv 
Clone the github repo, and cd to root

```bash
poetry install
poetry shell
jupyter lab

```