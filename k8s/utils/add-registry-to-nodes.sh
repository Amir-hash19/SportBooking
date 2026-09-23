for node in \
  devops-lab-control-plane \
  devops-lab-worker \
  devops-lab-worker2
do
  docker exec "$node" mkdir -p /etc/containerd/certs.d/localhost:5000

  docker exec "$node" sh -c 'cat > /etc/containerd/certs.d/localhost:5000/hosts.toml <<EOF
server = "http://kind-registry:5000"

[host."http://kind-registry:5000"]
  capabilities = ["pull", "resolve", "push"]
EOF'
done
