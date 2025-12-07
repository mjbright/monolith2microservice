
# 0. SETUP

TODO: Separate demo slides ...
- Monoliths
- Cluster
- Pod/Namespaces/Services
- Deploy/Namespaces/Services





- Re-create zip
- Test TG-AWS creation
  - VMs (cp+wo) 
  - add cp2/cp3/lb
  - setup Guacamole machine in case

# Done

- check "Add COLORS"
- Update ascii() on quiz app.py

# Rebuild all images
- rename online_shop.py to app.py ?

- then test images on Orbstack
  - test cli
  - test webUI

- then test images on kubefm1 cluster
  - test cli
  - test webUI


# 1. Intro: 22 -> 65 (incl, Pods)

Just theory(?)

# 2. Pod/Namespaces

-> Draw architecture:
   Cluster => Nodes (CP, Worker) => Pods (C.E. / Containers)

- Archive yaml files
  - for 2.Pod/Namespaces
    cover options: multi-container, shareProcessNamespace, multi init-container
  - update Pod image (?)
  - update other Pod characteristics (kubectl replace -f yaml -force)

Pod accessibility from Nodes or Pods
Service export
Choice of multi-container design
Pod deletion
Expose Pod as a (ClusterIP/NodePort) Service

# LATER:

Improve styling of quiz/survey apps -> different for v1, v2, v3

# 3. [Cluster setup] Deployments, Services

- Show token, gpg keys, apt repo list files

Apps:
- Expose Deployment as a (ClusterIP/NodePort) Service
- Scale up/down
- Pod deletion
- Pod isolation

# 4. Architecture

- demo etcdctl.fn
- add resource values to quiz/survey/store
  - req/limits
  - limitrange
  - resourcequota (req/lim, number of xxx)

# 5. API Access

- script up obtention of cert/keys
- better: kubectl proxy
- kubectl get --raw /api/v1/pods
- kubectl get --raw /api/v1/namespaces/pods
- kubectl get --raw /apis/app/v1/deployments
- kubectl get --raw /apis/app/v1/namespaces/deployments
- ~/.kube/cache/discovery/server_port/ ...

# 6. API Objects

- Deploy/ReplicaSet, DaemonSet, StatefulSet, Job/CronJob
- later HPA

# 7. "Managing State w. Deployments" - App Updates

- Re-create k1s.py demo using new flask apps ...

# 8. Helm / Kustomize

- Create Helm chart for each app
- Deploy apps from yaml using Kustomize, e.g. to quiz-dev, quiz-staging, quiz-prod
- Create Helm template | kustomize

- HPA v2 !!

# 9. Volumes / CM / Secrets

- emptyDir + ro fs for logs, for db
- hostPath + ro fs for logs, for db
- PV/PVC with statefulSet? and dynamic nfs

# 10. Services

- CIP, iptables, trafficPolicy
- NodePort
- LoadBalancer
- ExternalDNS?

# 11. Ingress

## 11a. Linkerd ServiceMesh

## 11b. Ingress
- route traffic to store/quiz/vote => use curl (& hostnames in /etc/hosts)
- route traffic to store/quiz/vote => url rewrite ?
- TLS?

# 11c. Gateway API
- route traffic to store/quiz/vote => use curl (& hostnames in /etc/hosts)
- route traffic to store/quiz/vote => url rewrite ?
- curl resolve ????, curl w/o resolve
- wget

???? HPA ????

# 12. Scheduling

Show existing redis-flask

LATER: separate front end from backend => spread out as per redis-flask demo
- adapt sqlite or redis as backend?

# 13. Log & TShoot

kubectl debug
- nodes
- pods (w different options)

Dashboard setup (show scripted of metrics-server, then dashboard)

# 14. CRDs

Create Quiz or Survey CRDs?

# 15. Security

- SecurityContext: ro fs, NET_RAW, user, fsGroup, ...
- PSS, audit logging
- user creation => then RBAC
- VAP, MAP
- Network Policies <= control frontend/backend communication
  - in app namespace, e.g. quiz
    allow ONLY
    - fe to middleware
    - allow middleware to db
    - demo cannot curl from outside
    - show variations
- kubectl debug Pod
  - RBAC permissions pods/ephemeral
    
# 16. HA

- just demo lab ... unless stars

