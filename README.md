# FLUIDOS kubectl plugin

This plugin is designed to simplify the utilisation of the meta-schedulers.
It operates as an additional utility that can be installed on the client side (operator machine).

## Requirements

The only assumption is to have python 3 installed, the plugin is tested with versions 3.10, 3.11, 3.12, and pypy 3.
Refer to [tox.ini](tox.ini) for details about which versions are being tested.


## How to install

To install the plugin simply execute:

`pip install git+https://github.com/fluidos-project/kubectl-fluidos-plugin`

The above command will install the package `kubectl-fluidos` module in the target environment.
It will also create a binary named `kubectl-fluidos` that should be available directly from command line.

## How to use

Once installed, the plugin is accessed by `kubectl` once the command `kubectl fluidos` is issued.

## Examples

### Example with MSPL

The support for MSPL is through analysis of the data being sent to the meta-orchestrator.
The pluging assumes that the endpoint runs on on the main node of the kubernetes cluster.
If no kubernetes context is available, or accessible, the plugin will default assuming the service is running on the host `localhost`, on port `8002`, over HTTP, at the endpointt called `/meservice`

For example, as per the following:
```
kubectl fluidis -f tests/dataset/test-mspl.xml
```

This behavior can be changed using the following options:

* `--mlps-hostname`, to change the hostname,
* `--mlps-port`, to change the port number,
* `--mlps-schema`, to change the schema, or
* `--mlps-url`, to update the entire URL, including method name.

### Example with Intent within manifest metadata

Alternatively, it is possible to specify intents via `metadata.annotations` using names beginning with the string  `fluidos-intent-`.

Using such annotations, one can request execution of the kubernetes entity specified in the manifest file to be limted to certain locations, i.e. `fluidos-intent-location: Germany`, compliance requirements, i.e. `fluidos-intent-compliance: HIPAA`, or requesting given performance requirements to be satisfied, i.e. `fluidos-intent-max-latency: 10ms` or `fluidos-intent-throughput: 100ops`.

For example, the following deployment enforces the creation of Pods within specific region of the infrastructure.

```
# Source: dlf-chart/charts/dataset-operator-chart/templates/apps/operator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dataset-operator
  annotations:
    fluidos-intent-location: Turin
    fluidos-intent-latency: 100ms
  labels:
    app.kubernetes.io/name: "dlf"
spec:
  replicas: 1
  selector:
    matchLabels:
      name: dataset-operator
  template:
    metadata:
      annotations:
        sidecar.istio.io/inject: "false"
      labels:
        name: dataset-operator
        app.kubernetes.io/name: "dlf"
    spec:
      containers:
        - name: dataset-operator
          # Replace this with the built image name
          image: "quay.io/datashim-io/dataset-operator:local"
          command:
            - /manager
          imagePullPolicy: Never
          ports:
            - containerPort: 9443
              name: webhook-api
```

This is achieved by invoking the following:

```
kubectl fluidos -f tests/dataset/test-deployment-with-intent.yaml
```

### Example of no requirement and fallback to normal behavior

If the manifest file provided to the plugin is neither defined using the MSPL language, or including a definition of intent, then it will be handled as if it was provided to the `apply` command. 

For example, the following manifest will not be handled directly by kubernetes.


```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  selector:
    matchLabels:
      app: nginx
  replicas: 2
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
```