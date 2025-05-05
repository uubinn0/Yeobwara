#!/usr/bin/env bash
# 사용법: 
# 1) 실행 권한 부여: chmod +x fix-k8s-network.sh
# 2) Control-plane 노드에서 실행: ./fix-k8s-network.sh
# 3) Worker 노드에서 실행:  ./fix-k8s-network.sh
set -e

# 수정할 값들
WORKER_EXTERNAL_IP="34.64.90.23"      # 워커 노드 외부 IP
APISERVER_HOST="k12b107.p.ssafy.io"  # API 서버 호스트
APISERVER_PORT="6443"                # API 서버 포트

if [ -f /etc/kubernetes/manifests/kube-apiserver.yaml ]; then
  echo "==> Control-plane 노드 감지됨: kube-apiserver manifest 업데이트"
  sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml.bak
  
  # 기존 flag 모두 삭제
  sudo sed -i '/--kubelet-preferred-address-types/d' /etc/kubernetes/manifests/kube-apiserver.yaml
  
  # 커맨드 바로 뒤에 ExternalIP 우선 flag 추가
  sudo sed -i "/- kube-apiserver/a\\    - --kubelet-preferred-address-types=ExternalIP,InternalIP,Hostname" /etc/kubernetes/manifests/kube-apiserver.yaml
  
  echo "kube-apiserver 재시작 대기 중..."
  kubectl get pods -n kube-system -l component=kube-apiserver --watch
  echo "Control-plane 설정 완료."
else
  echo "==> Worker 노드 감지됨: kubelet --node-ip 설정"
  sudo mkdir -p /etc/systemd/system/kubelet.service.d
  
  # drop-in 파일에 외부 IP로 설정
  sudo tee /etc/systemd/system/kubelet.service.d/20-node-ip.conf <<EOF
[Service]
Environment="KUBELET_EXTRA_ARGS=--node-ip=${WORKER_EXTERNAL_IP}"
EOF
  
  sudo systemctl daemon-reload
  sudo systemctl restart kubelet
  echo "✅ Worker 노드 설정 완료."
fi 