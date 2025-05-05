variable "project_id" {
  description = "GCP 프로젝트 ID"
  type        = string
  default     = "pure-wall-454723-t7"
}

variable "region" {
  description = "GCP 리전"
  type        = string
  default     = "asia-northeast3"
}

variable "zone" {
  description = "GCP 존"
  type        = string
  default     = "asia-northeast3-a"
}

variable "ssh_pub" {
  description = "로컬 SSH 공개키 경로"
  type        = string
  default     = "~/.ssh/my-gcp-key.pub"
}

variable "join_command" {
  description = "kubeadm join 명령어"
  type        = string
}
