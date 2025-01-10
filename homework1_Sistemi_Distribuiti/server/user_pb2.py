# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: user.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'user.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nuser.proto\x12\x04user\"[\n\x13RegisterUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x0e\n\x06ticker\x18\x02 \x01(\t\x12\x11\n\tlow_value\x18\x03 \x01(\x02\x12\x12\n\nhigh_value\x18\x04 \x01(\x02\"Y\n\x11UpdateUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x0e\n\x06ticker\x18\x02 \x01(\t\x12\x11\n\tlow_value\x18\x03 \x01(\x02\x12\x12\n\nhigh_value\x18\x04 \x01(\x02\"\"\n\x11\x44\x65leteUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"N\n\x16UpdateThresholdRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x11\n\tlow_value\x18\x02 \x01(\x02\x12\x12\n\nhigh_value\x18\x03 \x01(\x02\"N\n\x16RemoveThresholdRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x11\n\tlow_value\x18\x02 \x01(\x02\x12\x12\n\nhigh_value\x18\x03 \x01(\x02\"\"\n\x0f\x43ommandResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x07\n\x05\x45mpty\"\x1d\n\x0c\x45mailRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"3\n\x13\x41verageStockRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\"4\n\x12StockValueResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x02\"\x1f\n\x0f\x41llDataResponse\x12\x0c\n\x04\x64\x61ta\x18\x01 \x03(\t2\xe2\x02\n\x12UserCommandService\x12@\n\x0cRegisterUser\x12\x19.user.RegisterUserRequest\x1a\x15.user.CommandResponse\x12<\n\nUpdateUser\x12\x17.user.UpdateUserRequest\x1a\x15.user.CommandResponse\x12<\n\nDeleteUser\x12\x17.user.DeleteUserRequest\x1a\x15.user.CommandResponse\x12\x46\n\x0fUpdateThreshold\x12\x1c.user.UpdateThresholdRequest\x1a\x15.user.CommandResponse\x12\x46\n\x0fRemoveThreshold\x12\x1c.user.RemoveThresholdRequest\x1a\x15.user.CommandResponse2\xd4\x01\n\x10UserQueryService\x12\x30\n\nGetAllData\x12\x0b.user.Empty\x1a\x15.user.AllDataResponse\x12\x41\n\x11GetLastStockValue\x12\x12.user.EmailRequest\x1a\x18.user.StockValueResponse\x12K\n\x14GetAverageStockValue\x12\x19.user.AverageStockRequest\x1a\x18.user.StockValueResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'user_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REGISTERUSERREQUEST']._serialized_start=20
  _globals['_REGISTERUSERREQUEST']._serialized_end=111
  _globals['_UPDATEUSERREQUEST']._serialized_start=113
  _globals['_UPDATEUSERREQUEST']._serialized_end=202
  _globals['_DELETEUSERREQUEST']._serialized_start=204
  _globals['_DELETEUSERREQUEST']._serialized_end=238
  _globals['_UPDATETHRESHOLDREQUEST']._serialized_start=240
  _globals['_UPDATETHRESHOLDREQUEST']._serialized_end=318
  _globals['_REMOVETHRESHOLDREQUEST']._serialized_start=320
  _globals['_REMOVETHRESHOLDREQUEST']._serialized_end=398
  _globals['_COMMANDRESPONSE']._serialized_start=400
  _globals['_COMMANDRESPONSE']._serialized_end=434
  _globals['_EMPTY']._serialized_start=436
  _globals['_EMPTY']._serialized_end=443
  _globals['_EMAILREQUEST']._serialized_start=445
  _globals['_EMAILREQUEST']._serialized_end=474
  _globals['_AVERAGESTOCKREQUEST']._serialized_start=476
  _globals['_AVERAGESTOCKREQUEST']._serialized_end=527
  _globals['_STOCKVALUERESPONSE']._serialized_start=529
  _globals['_STOCKVALUERESPONSE']._serialized_end=581
  _globals['_ALLDATARESPONSE']._serialized_start=583
  _globals['_ALLDATARESPONSE']._serialized_end=614
  _globals['_USERCOMMANDSERVICE']._serialized_start=617
  _globals['_USERCOMMANDSERVICE']._serialized_end=971
  _globals['_USERQUERYSERVICE']._serialized_start=974
  _globals['_USERQUERYSERVICE']._serialized_end=1186
# @@protoc_insertion_point(module_scope)
