#!/bin/bash

NODE_ID=$(uuidgen)
NODE_ID="-Dnode.id=${NODE_ID}"
COORDINATOR_PORT=${COORDINATOR_PORT:-8080}
QUERY=${QUERY:-"show tables;"}

hostname
env

# set default value if the variable isn't set (testing outside of batch environment).
AWS_BATCH_JOB_NUM_NODES=${AWS_BATCH_JOB_NUM_NODES:-1}

if [ $AWS_BATCH_JOB_MAIN_NODE_INDEX -eq $AWS_BATCH_JOB_NODE_INDEX ]
then
  echo "Running Coordinator"
  ETC_DIR="/usr/lib/presto/default/etc/coordinator"
  DISCOVERY_URI="-Ddiscovery.uri=http://localhost:${COORDINATOR_PORT}"
  # /usr/lib/presto/bin/launcher start $NODE_ID $DISCOVERY_URI --etc-dir $ETC_DIR
  /usr/lib/presto/bin/launcher run $NODE_ID $DISCOVERY_URI --etc-dir $ETC_DIR

  # Loop until local server comes online.
  rc=-1
  while [ $rc -ne 0 ]
  do
    sleep 1
    curl http://localhost:8080/v1/info
    rc=$?
  done

  # Loop until all worker servers are online.
  # Even when curl returns successful (0) I get the following error
  # Query 20201001_154531_00000_sd57e failed: Presto server is still initializing
  sleep 1

  # Loop to see if any workers have come online.
  node_cnt=$(presto --execute "select count(*) from system.runtime.nodes;")
  echo "Node count: $node_cnt"

  # Need to use some character, such as "X" so string compare won't fail when
  # $node_cnt is blank
  while [ 'X'$node_cnt != 'X'\"$AWS_BATCH_JOB_NUM_NODES\" ]
  do
    sleep 5
    node_cnt=$(presto --execute "select count(*) from system.runtime.nodes;")
    echo "Node count: $node_cnt"
  done

  echo "Running: $QUERY"
  presto --catalog hive --schema default --execute "$QUERY"


else
  echo "Running Worker"
  ETC_DIR="/usr/lib/presto/default/etc/worker"
  DISCOVERY_URI="-Ddiscovery.uri=http://${AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS}:${COORDINATOR_PORT}/"
  echo "Usering Disovery_uri: $DISCOVERY_URI"
  /usr/lib/presto/bin/launcher run $NODE_ID $DISCOVERY_URI --etc-dir $ETC_DIR
fi
