#!/bin/bash
# AWS EC2 Deployment Script for NBA Decision Engine
# Run this on your EC2 instance after SSH-ing in

set -e

echo "🚀 Starting NBA Decision Engine deployment..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
echo "📚 Installing Git..."
sudo yum install -y git

# Clone repository
echo "📥 Cloning repository..."
cd /home/ec2-user
if [ -d "nba-decision-engine" ]; then
    echo "Repository exists, pulling latest..."
    cd nba-decision-engine
    git pull
else
    git clone https://github.com/BharathPalanisamy/NBA-decision-Engine.git nba-decision-engine
    cd nba-decision-engine
fi

# Build Docker image
echo "🏗️  Building Docker image..."
docker build -t nba-decision-engine .

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker stop nba-app 2>/dev/null || true
docker rm nba-app 2>/dev/null || true

# Run container
echo "▶️  Starting application..."
docker run -d \
    --name nba-app \
    -p 80:8501 \
    --restart unless-stopped \
    nba-decision-engine

# Wait for container to start
echo "⏳ Waiting for application to start..."
sleep 5

# Check status
if docker ps | grep -q nba-app; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Application is running!"
    echo "📍 Access it at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
    echo ""
    echo "📊 View logs: docker logs -f nba-app"
    echo "🔄 Update app: cd nba-decision-engine && git pull && docker build -t nba-decision-engine . && docker restart nba-app"
else
    echo "❌ Deployment failed. Check logs: docker logs nba-app"
    exit 1
fi
