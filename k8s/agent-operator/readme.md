# 00-namespace.yaml 필요이유 

- agent-operator 같은 파드가 쿠버네티스 안에서 다른 파드를 만들거나 지우려면, 쿠버네티스 API 서버에 요청을 보내야
- 아무 파드나 API 호출하면 보안 문제 발생 > agent-operator = ServiceAccount 라고 신분증 내미는 것
- ServiceAccount가 없으면 > 권한이 없다고 실패
```
Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:default:default" cannot create resource "pods"
```

기본 계정(default)으로는 대부분의 "만들기/지우기" 같은 행위가 막혀 있음

# 01-agent-operator-rabc.yaml 필요이유 
- ServiceAccount: agent-operator 같은 파드가 쿠버네티스 리소스를 조작하려면, 인증된 신분이 필요함
- Role: 어떤 리소스를 어디까지 할 수 있는지 정하는 권한 목록 (ex. pods, services를 만들고 지우고 수정할 수 있음)
- RoleBinding: 위에서 만든 Role을 특정 ServiceAccount에 연결해서 실제 권한을 부여함
- 이 세 가지가 모두 있어야 파드가 쿠버네티스 API에 접근할 수 있음, 없으면 위와 동일한 에러 발생 

# 02-agent-operator-deploy.yaml
