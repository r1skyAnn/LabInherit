#!/bin/bash
# 生成 JWT 密钥的辅助脚本

echo "生成 32 位随机 JWT 密钥："
echo ""
openssl rand -hex 32
echo ""
echo "将上述密钥复制到 backend/.env 的 JWT_SECRET 配置项"
