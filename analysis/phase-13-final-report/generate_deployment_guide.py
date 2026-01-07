#!/usr/bin/env python3
"""
Production Deployment Guide Generator
Shark Bake-Off: Phase 13

Generates step-by-step production deployment guide.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class DeploymentGuideGenerator:
    """Generates production deployment guide"""

    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.winner = None

    def load_decision_data(self, phase_c_dir: Path):
        """Load final decision data"""
        print(f"Loading decision data from {phase_c_dir}...")

        scores_file = phase_c_dir / 'final_scores.json'
        if scores_file.exists():
            with open(scores_file, 'r') as f:
                data = json.load(f)
                if 'final_scores' in data:
                    scores = [(name, info['total_score'])
                             for name, info in data['final_scores'].items()]
                    scores.sort(key=lambda x: x[1], reverse=True)

                    if len(scores) >= 1:
                        self.winner = scores[0][0]
                        print(f"  Winner: {self.winner}")

    def generate_guide(self):
        """Generate deployment guide"""
        print(f"\nGenerating deployment guide: {self.output_file}")

        with open(self.output_file, 'w') as f:
            # Title
            f.write("# Production Deployment Guide\n\n")
            f.write("## Shark Knowledge Base System\n\n")
            f.write(f"**Database:** {self.winner.title() if self.winner else '[Selected Database]'}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Table of Contents
            self._write_table_of_contents(f)

            # Main sections
            self._write_prerequisites(f)
            self._write_infrastructure_requirements(f)
            self._write_database_installation(f)
            self._write_database_configuration(f)
            self._write_dataset_loading(f)
            self._write_application_deployment(f)
            self._write_caching_setup(f)
            self._write_monitoring_alerting(f)
            self._write_backup_disaster_recovery(f)
            self._write_performance_validation(f)
            self._write_curation_tools(f)
            self._write_rollback_plan(f)
            self._write_go_live_checklist(f)
            self._write_post_deployment(f)
            self._write_troubleshooting(f)

        print(f"✓ Deployment guide generated: {self.output_file}")

    def _write_table_of_contents(self, f):
        """Write table of contents"""
        f.write("## Table of Contents\n\n")
        f.write("1. [Prerequisites](#prerequisites)\n")
        f.write("2. [Infrastructure Requirements](#infrastructure-requirements)\n")
        f.write("3. [Database Installation](#database-installation)\n")
        f.write("4. [Database Configuration](#database-configuration)\n")
        f.write("5. [Dataset Loading](#dataset-loading)\n")
        f.write("6. [Application Deployment](#application-deployment)\n")
        f.write("7. [Caching Setup](#caching-setup)\n")
        f.write("8. [Monitoring & Alerting](#monitoring--alerting)\n")
        f.write("9. [Backup & Disaster Recovery](#backup--disaster-recovery)\n")
        f.write("10. [Performance Validation](#performance-validation)\n")
        f.write("11. [Curation Tools](#curation-tools)\n")
        f.write("12. [Rollback Plan](#rollback-plan)\n")
        f.write("13. [Go-Live Checklist](#go-live-checklist)\n")
        f.write("14. [Post-Deployment](#post-deployment)\n")
        f.write("15. [Troubleshooting](#troubleshooting)\n\n")
        f.write("---\n\n")

    def _write_prerequisites(self, f):
        """Write prerequisites section"""
        f.write("## 1. Prerequisites\n\n")
        f.write("### Required Skills\n\n")
        f.write("- **Database Administration:** Experience with ")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("PostgreSQL\n")
        elif self.winner and self.winner.lower() in ['neo4j', 'memgraph']:
            f.write("graph databases (Cypher query language)\n")
        else:
            f.write("database administration\n")
        f.write("- **DevOps:** Linux system administration, Docker/containers\n")
        f.write("- **Networking:** Firewall configuration, security groups\n")
        f.write("- **Application Deployment:** Rust application deployment\n\n")

        f.write("### Required Access\n\n")
        f.write("- Cloud provider account (AWS/Azure/GCP) or on-premises infrastructure\n")
        f.write("- SSH access to servers\n")
        f.write("- Database administration credentials\n")
        f.write("- Firewall/security group modification permissions\n\n")

        f.write("### Required Software (Local Machine)\n\n")
        f.write("- SSH client\n")
        f.write("- Database client tools\n")
        f.write("- Git\n")
        f.write("- Docker (for local testing)\n\n")

        f.write("---\n\n")

    def _write_infrastructure_requirements(self, f):
        """Write infrastructure requirements section"""
        f.write("## 2. Infrastructure Requirements\n\n")

        f.write("### Database Server\n\n")
        f.write("**Hardware Specifications:**\n\n")
        f.write("- **CPU:** 8+ cores @ 2.4GHz (16 cores recommended for production)\n")
        f.write("- **RAM:** 16GB minimum")
        if self.winner and self.winner.lower() == 'memgraph':
            f.write(" (32GB recommended for headroom)\n")
        else:
            f.write(" (32GB+ recommended)\n")
        f.write("- **Storage:** 500GB SSD (NVMe preferred)\n")
        f.write("- **Network:** 1Gbps+ connectivity\n\n")

        f.write("**Operating System:**\n\n")
        f.write("- Ubuntu 22.04 LTS (recommended)\n")
        f.write("- RHEL 9 (alternative)\n")
        f.write("- Debian 12 (alternative)\n\n")

        f.write("### Application Server\n\n")
        f.write("**Hardware Specifications:**\n\n")
        f.write("- **CPU:** 4+ cores\n")
        f.write("- **RAM:** 8GB minimum (16GB recommended)\n")
        f.write("- **Storage:** 100GB SSD\n")
        f.write("- **Network:** 1Gbps+ connectivity\n\n")

        f.write("**Operating System:**\n\n")
        f.write("- Ubuntu 22.04 LTS (recommended)\n\n")

        f.write("### Redis Cache Server (If Using Caching)\n\n")
        f.write("**Hardware Specifications:**\n\n")
        f.write("- **CPU:** 2+ cores\n")
        f.write("- **RAM:** 4GB minimum (8GB recommended)\n")
        f.write("- **Storage:** 50GB SSD\n\n")

        f.write("### Network Configuration\n\n")
        f.write("**Firewall Rules:**\n\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("- PostgreSQL: Port 5432 (from application server only)\n")
        elif self.winner and self.winner.lower() in ['neo4j', 'memgraph']:
            f.write("- Bolt Protocol: Port 7687 (from application server only)\n")
        f.write("- Application API: Port 8080 (from load balancer/users)\n")
        f.write("- Redis: Port 6379 (from application server only)\n")
        f.write("- SSH: Port 22 (from admin IPs only)\n")
        f.write("- Monitoring: Ports 9090, 3000 (Prometheus, Grafana)\n\n")

        f.write("---\n\n")

    def _write_database_installation(self, f):
        """Write database installation section"""
        f.write("## 3. Database Installation\n\n")

        if self.winner and self.winner.lower() == 'postgresql':
            self._write_postgresql_installation(f)
        elif self.winner and self.winner.lower() == 'neo4j':
            self._write_neo4j_installation(f)
        elif self.winner and self.winner.lower() == 'memgraph':
            self._write_memgraph_installation(f)
        else:
            f.write("**Installation steps for selected database:**\n\n")
            f.write("[Database-specific installation instructions]\n\n")

        f.write("---\n\n")

    def _write_postgresql_installation(self, f):
        """PostgreSQL installation steps"""
        f.write("### PostgreSQL 16.1 Installation\n\n")
        f.write("**Step 1: Update system**\n\n")
        f.write("```bash\n")
        f.write("sudo apt update && sudo apt upgrade -y\n")
        f.write("```\n\n")

        f.write("**Step 2: Add PostgreSQL repository**\n\n")
        f.write("```bash\n")
        f.write("sudo sh -c 'echo \"deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main\" > /etc/apt/sources.list.d/pgdg.list'\n")
        f.write("wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -\n")
        f.write("sudo apt update\n")
        f.write("```\n\n")

        f.write("**Step 3: Install PostgreSQL**\n\n")
        f.write("```bash\n")
        f.write("sudo apt install -y postgresql-16 postgresql-contrib-16\n")
        f.write("```\n\n")

        f.write("**Step 4: Verify installation**\n\n")
        f.write("```bash\n")
        f.write("sudo systemctl status postgresql\n")
        f.write("psql --version  # Should show PostgreSQL 16.1\n")
        f.write("```\n\n")

    def _write_neo4j_installation(self, f):
        """Neo4j installation steps"""
        f.write("### Neo4j Community 5.15 Installation\n\n")
        f.write("**Step 1: Install Java (required for Neo4j)**\n\n")
        f.write("```bash\n")
        f.write("sudo apt update\n")
        f.write("sudo apt install -y openjdk-17-jdk\n")
        f.write("java -version  # Verify Java 17 installed\n")
        f.write("```\n\n")

        f.write("**Step 2: Add Neo4j repository**\n\n")
        f.write("```bash\n")
        f.write("wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -\n")
        f.write("echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list\n")
        f.write("sudo apt update\n")
        f.write("```\n\n")

        f.write("**Step 3: Install Neo4j**\n\n")
        f.write("```bash\n")
        f.write("sudo apt install -y neo4j=1:5.15.0\n")
        f.write("```\n\n")

        f.write("**Step 4: Configure and start Neo4j**\n\n")
        f.write("```bash\n")
        f.write("sudo systemctl enable neo4j\n")
        f.write("sudo systemctl start neo4j\n")
        f.write("sudo systemctl status neo4j\n")
        f.write("```\n\n")

        f.write("**Step 5: Set initial password**\n\n")
        f.write("```bash\n")
        f.write("# Wait for Neo4j to start, then set password\n")
        f.write("sudo neo4j-admin dbms set-initial-password YourSecurePassword123!\n")
        f.write("```\n\n")

    def _write_memgraph_installation(self, f):
        """Memgraph installation steps"""
        f.write("### Memgraph 2.14 Installation\n\n")
        f.write("**Step 1: Download Memgraph**\n\n")
        f.write("```bash\n")
        f.write("wget https://download.memgraph.com/memgraph/v2.14.0/ubuntu-22.04/memgraph_2.14.0-1_amd64.deb\n")
        f.write("```\n\n")

        f.write("**Step 2: Install Memgraph**\n\n")
        f.write("```bash\n")
        f.write("sudo dpkg -i memgraph_2.14.0-1_amd64.deb\n")
        f.write("```\n\n")

        f.write("**Step 3: Start Memgraph**\n\n")
        f.write("```bash\n")
        f.write("sudo systemctl enable memgraph\n")
        f.write("sudo systemctl start memgraph\n")
        f.write("sudo systemctl status memgraph\n")
        f.write("```\n\n")

        f.write("**Step 4: Verify installation**\n\n")
        f.write("```bash\n")
        f.write("# Connect using mgconsole\n")
        f.write("sudo apt install -y mgconsole\n")
        f.write("mgconsole --host 127.0.0.1 --port 7687\n")
        f.write("```\n\n")

    def _write_database_configuration(self, f):
        """Write database configuration section"""
        f.write("## 4. Database Configuration\n\n")

        if self.winner and self.winner.lower() == 'postgresql':
            f.write("### Apply Optimized PostgreSQL Configuration\n\n")
            f.write("**Configuration file location:** `/etc/postgresql/16/main/postgresql.conf`\n\n")
            f.write("**Optimized settings (from Phase A):**\n\n")
            f.write("```conf\n")
            f.write("# Memory Settings\n")
            f.write("shared_buffers = 4GB\n")
            f.write("effective_cache_size = 12GB\n")
            f.write("work_mem = 64MB\n")
            f.write("maintenance_work_mem = 1GB\n\n")
            f.write("# Query Planning\n")
            f.write("random_page_cost = 1.1  # SSD optimization\n")
            f.write("effective_io_concurrency = 200\n")
            f.write("max_parallel_workers_per_gather = 4\n")
            f.write("max_worker_processes = 8\n\n")
            f.write("# Connection Settings\n")
            f.write("max_connections = 200\n\n")
            f.write("# Logging\n")
            f.write("log_min_duration_statement = 1000  # Log queries > 1s\n")
            f.write("```\n\n")

        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("### Apply Optimized Neo4j Configuration\n\n")
            f.write("**Configuration file location:** `/etc/neo4j/neo4j.conf`\n\n")
            f.write("**Optimized settings (from Phase A):**\n\n")
            f.write("```conf\n")
            f.write("# Memory Settings\n")
            f.write("dbms.memory.heap.initial_size=4G\n")
            f.write("dbms.memory.heap.max_size=4G\n")
            f.write("dbms.memory.pagecache.size=8G\n\n")
            f.write("# Query Settings\n")
            f.write("dbms.query_cache_size=10000\n")
            f.write("dbms.threads.worker_count=16\n\n")
            f.write("# Network Settings\n")
            f.write("dbms.connector.bolt.listen_address=0.0.0.0:7687\n")
            f.write("dbms.connector.http.listen_address=0.0.0.0:7474\n\n")
            f.write("# Security\n")
            f.write("dbms.security.auth_enabled=true\n")
            f.write("```\n\n")

        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("### Apply Optimized Memgraph Configuration\n\n")
            f.write("**Configuration file location:** `/etc/memgraph/memgraph.conf`\n\n")
            f.write("**Optimized settings (from Phase A):**\n\n")
            f.write("```conf\n")
            f.write("--memory-limit=12GB\n")
            f.write("--memory-warning-threshold=10GB\n")
            f.write("--query-plan-cache-size=10000\n")
            f.write("--bolt-num-workers=16\n")
            f.write("--bolt-port=7687\n")
            f.write("--log-level=WARNING\n")
            f.write("```\n\n")

        f.write("**Restart database to apply configuration:**\n\n")
        f.write("```bash\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("sudo systemctl restart postgresql\n")
        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("sudo systemctl restart neo4j\n")
        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("sudo systemctl restart memgraph\n")
        f.write("```\n\n")

        f.write("---\n\n")

    def _write_dataset_loading(self, f):
        """Write dataset loading section"""
        f.write("## 5. Dataset Loading\n\n")
        f.write("### Generate Dataset\n\n")
        f.write("**On your local machine (or jump box):**\n\n")
        f.write("```bash\n")
        f.write("cd data/generators\n\n")
        f.write("# Generate 200,000 entities\n")
        f.write("python3 generate_air_data.py --count 140000 --output air_instances.csv\n")
        f.write("python3 generate_surface_data.py --count 50000 --output surface_instances.csv\n")
        f.write("python3 generate_ground_data.py --count 10000 --output ground_instances.csv\n")
        f.write("```\n\n")

        f.write("### Load Dataset\n\n")
        f.write("**Transfer data files to database server:**\n\n")
        f.write("```bash\n")
        f.write("scp *.csv user@database-server:/tmp/\n")
        f.write("```\n\n")

        f.write("**Load data into database:**\n\n")
        f.write("```bash\n")
        f.write("cd data/loaders\n\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("python3 load_postgresql.py \\\n")
            f.write("  --host database-server \\\n")
            f.write("  --port 5432 \\\n")
            f.write("  --database sharkdb \\\n")
            f.write("  --user shark \\\n")
            f.write("  --air-file /tmp/air_instances.csv \\\n")
            f.write("  --surface-file /tmp/surface_instances.csv \\\n")
            f.write("  --ground-file /tmp/ground_instances.csv\n")
        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("python3 load_neo4j.py \\\n")
            f.write("  --uri bolt://database-server:7687 \\\n")
            f.write("  --user neo4j \\\n")
            f.write("  --password YourPassword \\\n")
            f.write("  --air-file /tmp/air_instances.csv \\\n")
            f.write("  --surface-file /tmp/surface_instances.csv \\\n")
            f.write("  --ground-file /tmp/ground_instances.csv\n")
        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("python3 load_memgraph.py \\\n")
            f.write("  --uri bolt://database-server:7687 \\\n")
            f.write("  --air-file /tmp/air_instances.csv \\\n")
            f.write("  --surface-file /tmp/surface_instances.csv \\\n")
            f.write("  --ground-file /tmp/ground_instances.csv\n")
        f.write("```\n\n")

        f.write("**Expected load time:** 5-10 minutes for 200,000 entities\n\n")

        f.write("### Verify Data Load\n\n")
        f.write("**Check entity counts:**\n\n")
        f.write("```bash\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("psql -U shark -d sharkdb -c \"SELECT COUNT(*) FROM air_instance_lookup;\"\n")
            f.write("psql -U shark -d sharkdb -c \"SELECT COUNT(*) FROM surface_instance_lookup;\"\n")
            f.write("psql -U shark -d sharkdb -c \"SELECT COUNT(*) FROM ground_instance_lookup;\"\n")
        elif self.winner and self.winner.lower() in ['neo4j', 'memgraph']:
            f.write("# Connect to database and run:\n")
            f.write("MATCH (a:Aircraft) RETURN count(a);  // Should return 140000\n")
            f.write("MATCH (s:Ship) RETURN count(s);      // Should return 50000\n")
            f.write("MATCH (g:GroundUnit) RETURN count(g); // Should return 10000\n")
        f.write("```\n\n")

        f.write("---\n\n")

    def _write_application_deployment(self, f):
        """Write application deployment section"""
        f.write("## 6. Application Deployment\n\n")

        f.write("### Install Rust\n\n")
        f.write("**On application server:**\n\n")
        f.write("```bash\n")
        f.write("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y\n")
        f.write("source $HOME/.cargo/env\n")
        f.write("rustc --version  # Should show 1.75+\n")
        f.write("```\n\n")

        f.write("### Clone Repository\n\n")
        f.write("```bash\n")
        f.write("git clone https://github.com/your-org/shark-bakeoff.git\n")
        f.write("cd shark-bakeoff/implementations/rust\n")
        f.write("```\n\n")

        f.write("### Configure Application\n\n")
        f.write("**Create `.env` file:**\n\n")
        f.write("```bash\n")
        f.write("cat > .env <<EOF\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("DATABASE_URL=postgresql://shark:password@database-server:5432/sharkdb\n")
        elif self.winner and self.winner.lower() in ['neo4j', 'memgraph']:
            f.write("NEO4J_URI=bolt://database-server:7687\n")
            if self.winner.lower() == 'neo4j':
                f.write("NEO4J_USER=neo4j\n")
                f.write("NEO4J_PASSWORD=YourPassword\n")
        f.write("REDIS_URL=redis://redis-server:6379\n")
        f.write("CACHE_TTL_SECONDS=300\n")
        f.write("KAFKA_BROKERS=kafka-server:9092\n")
        f.write("LOG_LEVEL=info\n")
        f.write("HOST=0.0.0.0\n")
        f.write("PORT=8080\n")
        f.write("EOF\n")
        f.write("```\n\n")

        f.write("### Build Application\n\n")
        f.write("```bash\n")
        f.write("cargo build --release\n")
        f.write("```\n\n")
        f.write("**Build time:** 5-10 minutes (first build)\n\n")

        f.write("### Create Systemd Service\n\n")
        f.write("**Create service file:**\n\n")
        f.write("```bash\n")
        f.write("sudo tee /etc/systemd/system/shark-api.service > /dev/null <<EOF\n")
        f.write("[Unit]\n")
        f.write("Description=Shark Knowledge Base API\n")
        f.write("After=network.target\n\n")
        f.write("[Service]\n")
        f.write("Type=simple\n")
        f.write("User=shark\n")
        f.write("WorkingDirectory=/home/shark/shark-bakeoff/implementations/rust\n")
        f.write("EnvironmentFile=/home/shark/shark-bakeoff/implementations/rust/.env\n")
        f.write("ExecStart=/home/shark/shark-bakeoff/implementations/rust/target/release/shark-api\n")
        f.write("Restart=on-failure\n")
        f.write("RestartSec=5s\n\n")
        f.write("[Install]\n")
        f.write("WantedBy=multi-user.target\n")
        f.write("EOF\n")
        f.write("```\n\n")

        f.write("### Start Application\n\n")
        f.write("```bash\n")
        f.write("sudo systemctl daemon-reload\n")
        f.write("sudo systemctl enable shark-api\n")
        f.write("sudo systemctl start shark-api\n")
        f.write("sudo systemctl status shark-api\n")
        f.write("```\n\n")

        f.write("### Verify Application\n\n")
        f.write("```bash\n")
        f.write("# Test health endpoint\n")
        f.write("curl http://localhost:8080/health\n\n")
        f.write("# Test query endpoint\n")
        f.write("curl http://localhost:8080/api/aircraft/mode_s/A12345\n")
        f.write("```\n\n")

        f.write("---\n\n")

    def _write_caching_setup(self, f):
        """Write caching setup section"""
        f.write("## 7. Caching Setup (Optional)\n\n")
        f.write("**Only required if Phase 12 mitigation determined caching necessary**\n\n")

        f.write("### Install Redis\n\n")
        f.write("**On Redis server:**\n\n")
        f.write("```bash\n")
        f.write("sudo apt update\n")
        f.write("sudo apt install -y redis-server\n")
        f.write("```\n\n")

        f.write("### Configure Redis\n\n")
        f.write("**Edit `/etc/redis/redis.conf`:**\n\n")
        f.write("```conf\n")
        f.write("# Bind to all interfaces (secure with firewall)\n")
        f.write("bind 0.0.0.0\n\n")
        f.write("# Memory management\n")
        f.write("maxmemory 2gb\n")
        f.write("maxmemory-policy allkeys-lru\n\n")
        f.write("# Persistence (RDB snapshots)\n")
        f.write("save 900 1\n")
        f.write("save 300 10\n")
        f.write("save 60 10000\n")
        f.write("```\n\n")

        f.write("### Start Redis\n\n")
        f.write("```bash\n")
        f.write("sudo systemctl enable redis-server\n")
        f.write("sudo systemctl restart redis-server\n")
        f.write("sudo systemctl status redis-server\n")
        f.write("```\n\n")

        f.write("### Verify Redis\n\n")
        f.write("```bash\n")
        f.write("redis-cli ping  # Should return \"PONG\"\n\n")
        f.write("# Check memory usage\n")
        f.write("redis-cli INFO memory\n")
        f.write("```\n\n")

        f.write("---\n\n")

    def _write_monitoring_alerting(self, f):
        """Write monitoring and alerting section"""
        f.write("## 8. Monitoring & Alerting\n\n")

        f.write("### Install Prometheus\n\n")
        f.write("```bash\n")
        f.write("# Download Prometheus\n")
        f.write("wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz\n")
        f.write("tar xvfz prometheus-*.tar.gz\n")
        f.write("sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus\n")
        f.write("```\n\n")

        f.write("### Configure Prometheus\n\n")
        f.write("**Create `/opt/prometheus/prometheus.yml`:**\n\n")
        f.write("```yaml\n")
        f.write("global:\n")
        f.write("  scrape_interval: 15s\n\n")
        f.write("scrape_configs:\n")
        f.write("  - job_name: 'shark-api'\n")
        f.write("    static_configs:\n")
        f.write("      - targets: ['localhost:8080']\n")
        f.write("```\n\n")

        f.write("### Install Grafana\n\n")
        f.write("```bash\n")
        f.write("sudo apt install -y grafana\n")
        f.write("sudo systemctl enable grafana-server\n")
        f.write("sudo systemctl start grafana-server\n")
        f.write("```\n\n")

        f.write("### Configure Alerts\n\n")
        f.write("**Critical Alerts:**\n\n")
        f.write("- p99 latency >100ms for identifier lookups\n")
        f.write("- Error rate >1%\n")
        f.write("- Database connection failures\n")
        f.write("- API unavailable\n\n")

        f.write("**Warning Alerts:**\n\n")
        f.write("- p99 latency >80ms for identifier lookups\n")
        f.write("- Cache hit rate <70% (if using Redis)\n")
        f.write("- Memory usage >80%\n")
        f.write("- Disk usage >80%\n\n")

        f.write("---\n\n")

    def _write_backup_disaster_recovery(self, f):
        """Write backup and disaster recovery section"""
        f.write("## 9. Backup & Disaster Recovery\n\n")

        f.write("### Backup Strategy\n\n")
        f.write("**Frequency:**\n")
        f.write("- Full backup: Daily at 2 AM\n")
        f.write("- Incremental backup: Every 6 hours\n\n")

        f.write("**Retention:**\n")
        f.write("- Daily backups: 30 days\n")
        f.write("- Weekly backups: 90 days\n")
        f.write("- Monthly backups: 1 year\n\n")

        if self.winner and self.winner.lower() == 'postgresql':
            f.write("### PostgreSQL Backup Script\n\n")
            f.write("**Create `/usr/local/bin/backup-postgres.sh`:**\n\n")
            f.write("```bash\n")
            f.write("#!/bin/bash\n")
            f.write("BACKUP_DIR=/backups/postgresql\n")
            f.write("DATE=$(date +%Y%m%d_%H%M%S)\n\n")
            f.write("# Full backup\n")
            f.write("pg_dump -U shark sharkdb | gzip > $BACKUP_DIR/sharkdb_$DATE.sql.gz\n\n")
            f.write("# Upload to S3 (or equivalent)\n")
            f.write("aws s3 cp $BACKUP_DIR/sharkdb_$DATE.sql.gz s3://backups/shark/\n\n")
            f.write("# Cleanup old backups (>30 days)\n")
            f.write("find $BACKUP_DIR -name '*.sql.gz' -mtime +30 -delete\n")
            f.write("```\n\n")

        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("### Neo4j Backup Script\n\n")
            f.write("**Create `/usr/local/bin/backup-neo4j.sh`:**\n\n")
            f.write("```bash\n")
            f.write("#!/bin/bash\n")
            f.write("BACKUP_DIR=/backups/neo4j\n")
            f.write("DATE=$(date +%Y%m%d_%H%M%S)\n\n")
            f.write("# Stop Neo4j\n")
            f.write("sudo systemctl stop neo4j\n\n")
            f.write("# Backup data directory\n")
            f.write("tar -czf $BACKUP_DIR/neo4j_$DATE.tar.gz /var/lib/neo4j/data\n\n")
            f.write("# Start Neo4j\n")
            f.write("sudo systemctl start neo4j\n\n")
            f.write("# Upload to S3\n")
            f.write("aws s3 cp $BACKUP_DIR/neo4j_$DATE.tar.gz s3://backups/shark/\n\n")
            f.write("# Cleanup\n")
            f.write("find $BACKUP_DIR -name '*.tar.gz' -mtime +30 -delete\n")
            f.write("```\n\n")

        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("### Memgraph Backup Script\n\n")
            f.write("**Create `/usr/local/bin/backup-memgraph.sh`:**\n\n")
            f.write("```bash\n")
            f.write("#!/bin/bash\n")
            f.write("BACKUP_DIR=/backups/memgraph\n")
            f.write("DATE=$(date +%Y%m%d_%H%M%S)\n\n")
            f.write("# Create snapshot via mgconsole\n")
            f.write("echo 'CREATE SNAPSHOT;' | mgconsole --host 127.0.0.1\n\n")
            f.write("# Backup snapshot directory\n")
            f.write("tar -czf $BACKUP_DIR/memgraph_$DATE.tar.gz /var/lib/memgraph/snapshots\n\n")
            f.write("# Upload to S3\n")
            f.write("aws s3 cp $BACKUP_DIR/memgraph_$DATE.tar.gz s3://backups/shark/\n\n")
            f.write("# Cleanup\n")
            f.write("find $BACKUP_DIR -name '*.tar.gz' -mtime +30 -delete\n")
            f.write("```\n\n")

        f.write("### Schedule Backups\n\n")
        f.write("**Add to crontab:**\n\n")
        f.write("```bash\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("0 2 * * * /usr/local/bin/backup-postgres.sh\n")
        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("0 2 * * * /usr/local/bin/backup-neo4j.sh\n")
        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("0 2 * * * /usr/local/bin/backup-memgraph.sh\n")
        f.write("```\n\n")

        f.write("### Disaster Recovery\n\n")
        f.write("**Recovery Time Objective (RTO):** 4 hours\n\n")
        f.write("**Recovery Point Objective (RPO):** 1 hour\n\n")

        f.write("**Recovery Steps:**\n")
        f.write("1. Provision new database server (if needed)\n")
        f.write("2. Install database software\n")
        f.write("3. Download latest backup from S3\n")
        f.write("4. Restore backup\n")
        f.write("5. Update application configuration\n")
        f.write("6. Verify data integrity\n")
        f.write("7. Resume operations\n\n")

        f.write("---\n\n")

    def _write_performance_validation(self, f):
        """Write performance validation section"""
        f.write("## 10. Performance Validation\n\n")

        f.write("### Smoke Test (1000 requests)\n\n")
        f.write("```bash\n")
        f.write("cd benchmark/harness\n\n")
        f.write("python3 runner.py http://app-server:8080 \\\n")
        f.write("  --pattern balanced-50 \\\n")
        f.write("  --requests 1000 \\\n")
        f.write("  --concurrency 10 \\\n")
        f.write("  --output smoke_test\n")
        f.write("```\n\n")

        f.write("**Expected Results:**\n")
        f.write("- p99 < 100ms for identifier lookups\n")
        f.write("- p99 < 300ms for two-hop traversals\n")
        f.write("- p99 < 500ms for three-hop traversals\n")
        f.write("- 0% error rate\n\n")

        f.write("### Load Test (50,000 requests)\n\n")
        f.write("```bash\n")
        f.write("python3 runner.py http://app-server:8080 \\\n")
        f.write("  --pattern balanced-50 \\\n")
        f.write("  --requests 50000 \\\n")
        f.write("  --concurrency 20 \\\n")
        f.write("  --output load_test\n")
        f.write("```\n\n")

        f.write("### Concurrency Test\n\n")
        f.write("```bash\n")
        f.write("# Test at 50 concurrent users\n")
        f.write("python3 runner.py http://app-server:8080 \\\n")
        f.write("  --pattern balanced-50 \\\n")
        f.write("  --requests 10000 \\\n")
        f.write("  --concurrency 50\n\n")
        f.write("# Test at 100 concurrent users\n")
        f.write("python3 runner.py http://app-server:8080 \\\n")
        f.write("  --pattern balanced-50 \\\n")
        f.write("  --requests 10000 \\\n")
        f.write("  --concurrency 100\n")
        f.write("```\n\n")

        f.write("---\n\n")

    def _write_curation_tools(self, f):
        """Write curation tools section"""
        f.write("## 11. Curation Tools\n\n")

        if self.winner and self.winner.lower() == 'postgresql':
            f.write("### Deploy pgAdmin\n\n")
            f.write("```bash\n")
            f.write("# Install pgAdmin\n")
            f.write("sudo apt install -y pgadmin4\n\n")
            f.write("# Configure access\n")
            f.write("# Access at http://server:5050\n")
            f.write("```\n\n")

        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("### Neo4j Browser (Included)\n\n")
            f.write("**Access Neo4j Browser:**\n\n")
            f.write("- URL: `http://database-server:7474`\n")
            f.write("- Username: `neo4j`\n")
            f.write("- Password: [Your configured password]\n\n")

            f.write("### Neo4j Bloom (Optional - Requires License)\n\n")
            f.write("For best-in-class visualization:\n")
            f.write("1. Contact Neo4j for commercial license\n")
            f.write("2. Install Bloom plugin\n")
            f.write("3. Configure curator access\n\n")

        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("### Memgraph Lab\n\n")
            f.write("**Install Memgraph Lab:**\n\n")
            f.write("```bash\n")
            f.write("# Download Lab\n")
            f.write("wget https://download.memgraph.com/memgraph-lab/v2.14.0/memgraph-lab-2.14.0-linux-x86_64.AppImage\n\n")
            f.write("# Make executable\n")
            f.write("chmod +x memgraph-lab-2.14.0-linux-x86_64.AppImage\n\n")
            f.write("# Run Lab\n")
            f.write("./memgraph-lab-2.14.0-linux-x86_64.AppImage\n")
            f.write("```\n\n")

            f.write("**Connect to Memgraph:**\n")
            f.write("- Host: `database-server`\n")
            f.write("- Port: `7687`\n")
            f.write("- No authentication required (Community Edition)\n\n")

        f.write("### Curator Training\n\n")
        f.write("**Week 5-6: Train curators on:**\n\n")
        f.write("1. Graph visualization and exploration\n")
        f.write("2. Adding properties to entities\n")
        f.write("3. Creating relationships\n")
        f.write("4. Running queries\n")
        f.write("5. Exporting data\n\n")

        f.write("---\n\n")

    def _write_rollback_plan(self, f):
        """Write rollback plan section"""
        f.write("## 12. Rollback Plan\n\n")

        f.write("### When to Rollback\n\n")
        f.write("Rollback if any of the following occur within 48 hours of go-live:\n\n")
        f.write("- p99 latency exceeds thresholds by >10%\n")
        f.write("- Error rate >1%\n")
        f.write("- Data corruption detected\n")
        f.write("- Critical application bugs\n\n")

        f.write("### Rollback Procedure\n\n")
        f.write("**Step 1: Stop new traffic**\n\n")
        f.write("```bash\n")
        f.write("# Update load balancer to redirect to old system\n")
        f.write("# Or stop Shark API\n")
        f.write("sudo systemctl stop shark-api\n")
        f.write("```\n\n")

        f.write("**Step 2: Restore previous system**\n\n")
        f.write("- Restore old database from backup\n")
        f.write("- Restore old application version\n")
        f.write("- Verify data integrity\n\n")

        f.write("**Step 3: Validate rollback**\n\n")
        f.write("```bash\n")
        f.write("# Run smoke test on old system\n")
        f.write("curl http://old-system:8080/health\n")
        f.write("```\n\n")

        f.write("**Step 4: Resume traffic**\n\n")
        f.write("- Update load balancer to old system\n")
        f.write("- Monitor for 1 hour\n\n")

        f.write("**Step 5: Post-mortem**\n\n")
        f.write("- Document rollback reason\n")
        f.write("- Identify root cause\n")
        f.write("- Create mitigation plan\n")
        f.write("- Schedule retry\n\n")

        f.write("---\n\n")

    def _write_go_live_checklist(self, f):
        """Write go-live checklist section"""
        f.write("## 13. Go-Live Checklist\n\n")

        f.write("### Pre-Launch (T-24 hours)\n\n")
        f.write("- [ ] Database optimized and running\n")
        f.write("- [ ] 200,000 entities loaded and verified\n")
        f.write("- [ ] Application deployed and tested\n")
        f.write("- [ ] Redis cache configured (if applicable)\n")
        f.write("- [ ] Monitoring and alerting active\n")
        f.write("- [ ] Backups configured and tested\n")
        f.write("- [ ] Load tests passed\n")
        f.write("- [ ] Rollback plan documented\n")
        f.write("- [ ] Stakeholders notified\n\n")

        f.write("### Launch Day (Week 7)\n\n")
        f.write("**Phase 1: 10% Traffic (Hour 0-4)**\n\n")
        f.write("- [ ] Route 10% of traffic to new system\n")
        f.write("- [ ] Monitor p99 latency every 15 minutes\n")
        f.write("- [ ] Monitor error rate\n")
        f.write("- [ ] Check cache hit rate (if using Redis)\n")
        f.write("- [ ] Verify all metrics within thresholds\n\n")

        f.write("**Phase 2: 50% Traffic (Hour 4-8)**\n\n")
        f.write("- [ ] Increase to 50% traffic\n")
        f.write("- [ ] Continue monitoring\n")
        f.write("- [ ] Verify no degradation\n\n")

        f.write("**Phase 3: 100% Traffic (Hour 8+)**\n\n")
        f.write("- [ ] Route 100% traffic to new system\n")
        f.write("- [ ] Intensive monitoring for 4 hours\n")
        f.write("- [ ] Verify all thresholds met\n")
        f.write("- [ ] Collect curator feedback\n\n")

        f.write("### Post-Launch (Day 1-2)\n\n")
        f.write("- [ ] 24-hour stability monitoring\n")
        f.write("- [ ] Daily performance reports\n")
        f.write("- [ ] Curator feedback sessions\n")
        f.write("- [ ] Issue tracking and resolution\n")
        f.write("- [ ] Fine-tune cache TTLs (if applicable)\n\n")

        f.write("---\n\n")

    def _write_post_deployment(self, f):
        """Write post-deployment section"""
        f.write("## 14. Post-Deployment\n\n")

        f.write("### Month 1: Intensive Monitoring\n\n")
        f.write("**Daily Activities:**\n")
        f.write("- Review p99 latency metrics\n")
        f.write("- Check error logs\n")
        f.write("- Monitor resource usage (CPU, memory, disk)\n")
        f.write("- Collect curator feedback\n\n")

        f.write("**Weekly Activities:**\n")
        f.write("- Performance report to stakeholders\n")
        f.write("- Issue review and prioritization\n")
        f.write("- Cache effectiveness analysis (if using Redis)\n\n")

        f.write("### Month 2-3: Optimization\n\n")
        f.write("**Fine-Tuning:**\n")
        f.write("- Adjust cache TTLs based on real traffic patterns\n")
        f.write("- Optimize slow queries identified in production\n")
        f.write("- Update database configuration if needed\n\n")

        f.write("**Training:**\n")
        f.write("- Advanced curator training sessions\n")
        f.write("- Best practices documentation\n\n")

        f.write("### Month 6: Review\n\n")
        f.write("**Validation:**\n")
        f.write("- Verify database choice still correct\n")
        f.write("- Review dataset growth trends\n")
        f.write("- Assess if scaling needed\n")
        f.write("- Document production learnings\n\n")

        f.write("**Planning:**\n")
        f.write("- Forecast next 12 months growth\n")
        f.write("- Plan infrastructure scaling if needed\n")
        if self.winner and self.winner.lower() == 'memgraph':
            f.write("- Monitor RAM usage (Memgraph limitation)\n")
        f.write("- Evaluate read replicas if needed\n\n")

        f.write("### Year 1: Long-Term Planning\n\n")
        f.write("**Growth Planning:**\n")
        f.write("- Dataset size projection\n")
        f.write("- Infrastructure scaling plan\n")
        if self.winner and self.winner.lower() == 'memgraph':
            f.write("- Migration plan if approaching RAM limit\n")
        f.write("- Budget for next year\n\n")

        f.write("---\n\n")

    def _write_troubleshooting(self, f):
        """Write troubleshooting section"""
        f.write("## 15. Troubleshooting\n\n")

        f.write("### Common Issues\n\n")

        f.write("#### Issue: High Latency\n\n")
        f.write("**Symptoms:** p99 >100ms for identifier lookups\n\n")
        f.write("**Possible Causes:**\n")
        f.write("- Database overloaded\n")
        f.write("- Slow disk I/O\n")
        f.write("- Network latency\n")
        f.write("- Missing indexes\n\n")

        f.write("**Solutions:**\n")
        f.write("1. Check database CPU/memory usage\n")
        f.write("2. Verify disk I/O with `iostat`\n")
        f.write("3. Check network latency with `ping`\n")
        f.write("4. Review slow query logs\n")
        f.write("5. Add indexes if needed\n\n")

        f.write("#### Issue: Database Connection Failures\n\n")
        f.write("**Symptoms:** Application cannot connect to database\n\n")
        f.write("**Solutions:**\n")
        f.write("1. Verify database is running: `systemctl status [database]`\n")
        f.write("2. Check firewall rules\n")
        f.write("3. Verify connection string in `.env`\n")
        f.write("4. Check database logs\n\n")

        if self.winner and self.winner.lower() in ['neo4j', 'memgraph']:
            f.write("#### Issue: Cache Not Helping\n\n")
            f.write("**Symptoms:** Cache hit rate <50%\n\n")
            f.write("**Solutions:**\n")
            f.write("1. Increase cache TTL\n")
            f.write("2. Warm up cache before load testing\n")
            f.write("3. Check query diversity (high diversity = low hit rate)\n")
            f.write("4. Consider caching more query types\n\n")

        if self.winner and self.winner.lower() == 'memgraph':
            f.write("#### Issue: Out of Memory (Memgraph)\n\n")
            f.write("**Symptoms:** Memgraph crashes, OOM errors\n\n")
            f.write("**Solutions:**\n")
            f.write("1. Check dataset size vs RAM\n")
            f.write("2. Increase server RAM\n")
            f.write("3. Archive old data\n")
            f.write("4. Consider migration to Neo4j (disk-based)\n\n")

        f.write("### Support Resources\n\n")
        f.write("**Database-Specific:**\n")
        if self.winner and self.winner.lower() == 'postgresql':
            f.write("- PostgreSQL Documentation: https://www.postgresql.org/docs/\n")
            f.write("- PostgreSQL Mailing Lists\n")
        elif self.winner and self.winner.lower() == 'neo4j':
            f.write("- Neo4j Documentation: https://neo4j.com/docs/\n")
            f.write("- Neo4j Community Forum\n")
        elif self.winner and self.winner.lower() == 'memgraph':
            f.write("- Memgraph Documentation: https://memgraph.com/docs/\n")
            f.write("- Memgraph Discord Community\n")

        f.write("\n**Project-Specific:**\n")
        f.write("- Implementation Team\n")
        f.write("- Database Administrator\n")
        f.write("- DevOps Engineer\n\n")

        f.write("---\n\n")
        f.write("**End of Production Deployment Guide**\n")


def main():
    parser = argparse.ArgumentParser(description="Generate production deployment guide")
    parser.add_argument("--phase-c", type=Path, required=True,
                       help="Path to Phase C decision results directory")
    parser.add_argument("--output", type=Path, default="PRODUCTION_DEPLOYMENT_GUIDE.md",
                       help="Output file path")

    args = parser.parse_args()

    print("="*80)
    print("SHARK BAKE-OFF: PRODUCTION DEPLOYMENT GUIDE GENERATOR")
    print("="*80 + "\n")

    generator = DeploymentGuideGenerator(args.output)

    try:
        # Load decision data
        generator.load_decision_data(args.phase_c)

        # Generate deployment guide
        generator.generate_guide()

        print("\n" + "="*80)
        print("✓ SUCCESS: Production deployment guide generated!")
        print("="*80)
        print(f"\nGuide location: {args.output}")
        print("\nTarget audience: Implementation teams, DBAs, DevOps")
        print("Sections: 15 comprehensive sections")

        return 0

    except Exception as e:
        print(f"\n✗ Error generating deployment guide: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
