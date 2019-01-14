# coding:UTF-8
# 2019-1-8
# freeze_graph

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

from google.protobuf import text_format

from tensorflow.core.framework import graph_pb2
from tensorflow.core.protobuf import saver_pb2
from tensorflow.python import pywrap_tensorflow
from tensorflow.python.client import session
from tensorflow.python.framework import graph_util
from tensorflow.python.framework import importer
from tensorflow.python.platform import app
from tensorflow.python.platform import gfile
from tensorflow.python.training import saver as saver_lib

import tensorflow as tf
input_para= None




def freeze_graph_with_def_protos(input_graph_def,
                                input_saver_def,
                                input_checkpoint,
                                output_node_names,
                                restore_op_name,
                                filename_tensor_name,
                                output_graph,
                                clear_devices,
                                initializer_nodes,
                                variable_names_blacklist=""):
    """
    Converts all variables in a graph and checkpoint into constants.
    """
    del restore_op_name, filename_tensor_name  # Unused by updated loading code.

    # 'input_checkpoint' may be a prefix if we're using Saver V2 format
    if not saver_lib.checkpoint_exists(input_checkpoint):
        print("Input checkpoint '" + input_checkpoint + "' doesn't exist!")
        return -1

    if not output_node_names:
        print("You need to supply the name of a node to --output_node_names.")
        return -1

    # Remove all the explicit device specifications for this node. This helps to
    # make the graph more portable.
    if clear_devices:
        for node in input_graph_def.node:
            node.device = ""

    _ = importer.import_graph_def(input_graph_def, name="")

    with session.Session() as sess:
        if input_saver_def:
            saver = saver_lib.Saver(saver_def=input_saver_def)
            saver.restore(sess, input_checkpoint)
        else:
            var_list = {}
            reader = pywrap_tensorflow.NewCheckpointReader(input_checkpoint)
            var_to_shape_map = reader.get_variable_to_shape_map()
            for key in var_to_shape_map:
                try:
                    tensor = sess.graph.get_tensor_by_name(key + ":0")
                except KeyError:
                    # This tensor doesn't exist in the graph (for example it's
                    # 'global_step' or a similar housekeeping element) so skip it.
                    print('error: ', key)
                    continue
                var_list[key] = tensor
            saver = saver_lib.Saver(var_list=var_list)
            saver.restore(sess, input_checkpoint)
            if initializer_nodes:
                sess.run(initializer_nodes)

        variable_names_blacklist = (variable_names_blacklist.split(",") if
                                variable_names_blacklist else None)
        output_graph_def = graph_util.convert_variables_to_constants(
            sess,
            input_graph_def,
            output_node_names.split(","),
            variable_names_blacklist=variable_names_blacklist)

    # Write GraphDef to file if output path has been given.
    if output_graph:
        with gfile.GFile(output_graph, "wb") as f:
            f.write(output_graph_def.SerializeToString())

    print("%d ops in the final graph." % len(output_graph_def.node))

    return output_graph_def


def _parse_input_graph_proto(input_graph, input_binary):
    """
    Parser input tensorflow graph into GraphDef proto.
    """
    if not gfile.Exists(input_graph):
        print("Input graph file '" + input_graph + "' does not exist!")
        return -1
    input_graph_def = graph_pb2.GraphDef()
    mode = "rb" if input_binary else "r"
    with gfile.FastGFile(input_graph, mode) as f:
        if input_binary:
            input_graph_def.ParseFromString(f.read())
        else:
            text_format.Merge(f.read(), input_graph_def)
    return input_graph_def


def _parse_input_saver_proto(input_saver, input_binary):
  """Parser input tensorflow Saver into SaverDef proto."""
  if not gfile.Exists(input_saver):
    print("Input saver file '" + input_saver + "' does not exist!")
    return -1
  mode = "rb" if input_binary else "r"
  with gfile.FastGFile(input_saver, mode) as f:
    saver_def = saver_pb2.SaverDef()
    if input_binary:
      saver_def.ParseFromString(f.read())
    else:
      text_format.Merge(f.read(), saver_def)
  return saver_def


def freeze_graph(input_graph,
                 input_saver,
                 input_binary,
                 input_checkpoint,
                 output_node_names,
                 restore_op_name,
                 filename_tensor_name,
                 output_graph,
                 clear_devices,
                 initializer_nodes,
                 variable_names_blacklist=""):
    """
    Converts all variables in a graph and checkpoint into constants.
    """
    input_graph_def = _parse_input_graph_proto(input_graph, input_binary)
    input_saver_def = None
    if input_saver:
        input_saver_def = _parse_input_saver_proto(input_saver, input_binary)
    freeze_graph_with_def_protos(
        input_graph_def,
        input_saver_def,
        input_checkpoint,
        output_node_names,
        restore_op_name,
        filename_tensor_name,
        output_graph,
        clear_devices,
        initializer_nodes,
        variable_names_blacklist)


def main(input_para):
    freeze_graph(
        input_para['input_graph'], 
        input_para['input_saver'], 
        input_para['input_binary'],
        input_para['input_checkpoint'], 
        input_para['output_node_names'],
        input_para['restore_op_name'], 
        input_para['filename_tensor_name'],
        input_para['output_graph'], 
        input_para['clear_devices'], 
        input_para['initializer_nodes'],
        input_para['variable_names_blacklist'])

if __name__ == '__main__':
    # test
    input_para = {
        # 'input_graph' : 'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/vgg_16_inf_graph.pb', # vgg
        # 'input_checkpoint' : r'C:\Study\github\others\Deep-Learning-21-Examples-master\chapter_3\data_prepare\satellite\train_dir_vgg\model.ckpt-602', # vgg
        # 'output_graph' : r'C:\Study\github\others\Deep-Learning-21-Examples-master\chapter_3\data_prepare\satellite\vgg_frozen_graph.pb', # vgg
        # 'output_node_names' : 'vgg_16/fc8/squeezed', # vgg node

        # 'input_graph' : 'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/nasnet_inf_graph.pb', # nasnet
        # 'input_checkpoint' : r'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/train_dir_nasnet_large\model.ckpt-141', # nasnet
        # 'output_graph' : r'C:\Study\github\others\Deep-Learning-21-Examples-master\chapter_3\data_prepare\satellite\nasnet_frozen_graph.pb', # nasnet
        # 'output_node_names' : 'final_layer/predictions', # nasnet

        # 'input_graph' : 'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/pnasnet_inf_graph.pb', # pnasnet
        # 'input_checkpoint' : r'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/train_dir_pnasnet_large\model.ckpt-135', # pnasnet
        # 'output_graph' : r'C:\Study\github\others\Deep-Learning-21-Examples-master\chapter_3\data_prepare\satellite\pnasnet_frozen_graph.pb', # pnasnet
        # 'output_node_names' : 'final_layer/predictions', # pnasnet


        'input_graph' : 'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/resnet_inf_graph.pb', # resnet
        'input_checkpoint' : r'C:/Study/github/others/Deep-Learning-21-Examples-master/chapter_3/data_prepare/satellite/train_dir_resnet\model.ckpt-135', # pnasnet
        'output_graph' : r'C:\Study\github\others\Deep-Learning-21-Examples-master\chapter_3\data_prepare\satellite\resnet_frozen_graph.pb', # pnasnet
        'output_node_names' : 'final_layer/predictions', # pnasnet


        'input_saver' : '',
        'input_binary' : True, # bool

        # 'output_node_names' : 'InceptionV3/Predictions/Reshape_1', # inception3 node

        'restore_op_name' : "save/restore_all",
        'filename_tensor_name' : "save/Const:0",
        'clear_devices' : True,
        'initializer_nodes' : '',
        'variable_names_blacklist' : '',
    }
    main(input_para)