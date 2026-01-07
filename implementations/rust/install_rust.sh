#!/bin/bash
# Install Rust toolchain for Shark Bake-Off Rust implementation

set -e

echo "Installing Rust via rustup..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Source cargo env
source "$HOME/.cargo/env"

echo ""
echo "Rust installation complete!"
echo "Run 'source \$HOME/.cargo/env' to update your current shell"
echo ""
echo "To build the project:"
echo "  cd implementations/rust"
echo "  cargo build --release"
echo ""
