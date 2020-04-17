import json
from segmenter import *
import os
import mock
from mock import call

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_ct_muscle_segment_nifti_calls_container_requester_send_to_worker_once(mock_send_req):

    mock_source_file = "/mock/filename.nii.gz"

    hostname     = os.environ["CT_MUSCLE_SEG_HOSTNAME"]
    port         = os.environ["CT_MUSCLE_SEG_PORT"]
    request_name = 'ct_segment_muscle'
    payload      = {'source_file': mock_source_file}

    mock_send_req.return_value = {"segmentation": "hello"}

    ct_muscle_segment_nifti(mock_source_file, filepath_only=True)

    mock_send_req.assert_called_once_with(payload, hostname, port, request_name)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_ct_muscle_segment_dcm_calls_container_requester_once_for_conversion_and_once_for_muscle_segment(mock_send_req):

    mock_source_dir = "/mock/dir"
    mock_source_file_converted = "mock_converted.nii.gz"

    muscle_seg_hostname     = os.environ["CT_MUSCLE_SEG_HOSTNAME"]
    muscle_seg_port         = os.environ["CT_MUSCLE_SEG_PORT"]
    muscle_seg_request_name = 'ct_segment_muscle'
    muscle_seg_payload      = {'source_file': mock_source_file_converted}

    converter_hostname     = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
    converter_port         = os.environ["LUNGMASK_CONVERTER_PORT"]
    converter_request_name = "lungmask_convert_dcm_to_nifti"
    converter_payload      = {'source_dir': mock_source_dir}


    mock_send_req.return_value = {
        "filename": mock_source_file_converted,
        "segmentation": "hello"
    }

    converter_call  = call(converter_payload,  converter_hostname,  converter_port,  converter_request_name)
    muscle_seg_call = call(muscle_seg_payload, muscle_seg_hostname, muscle_seg_port, muscle_seg_request_name)

    calls = [converter_call, muscle_seg_call]

    ct_muscle_segment_dcm(mock_source_dir, filepath_only=True)

    # mock_send_req.assert_called_once_with(payload, hostname, port, request_name)
    mock_send_req.assert_has_calls(calls, any_order=False)


@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_ct_visceral_fat_nifti_calls_container_requester_send_to_worker_once(mock_send_req):

    mock_source_file = "/mock/filename.nii.gz"

    hostname     = os.environ["CT_FAT_MEASURE_HOSTNAME"]
    port         = os.environ["CT_FAT_MEASURE_PORT"]
    request_name = 'ct_visceral_fat_nifti'
    payload      = {'source_file': mock_source_file}

    mock_send_req.return_value = {"fat_report": "hello"}

    ct_fat_measure_nifti(mock_source_file, filepath_only=True)

    mock_send_req.assert_called_once_with(payload, hostname, port, request_name)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_ct_visceral_fat_dcm_calls_container_requester_send_once_for_conversion_and_once_for_fat_measure(mock_send_req):

    mock_source_dir = "/mock/dir"
    mock_source_file_converted = "/mock/conv.nii.gz"

    ct_hostname     = os.environ["CT_FAT_MEASURE_HOSTNAME"]
    ct_port         = os.environ["CT_FAT_MEASURE_PORT"]
    ct_request_name = 'ct_visceral_fat_nifti'
    ct_payload      = {'source_file': mock_source_file_converted}

    converter_hostname     = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
    converter_port         = os.environ["LUNGMASK_CONVERTER_PORT"]
    converter_request_name = "lungmask_convert_dcm_to_nifti"
    converter_payload      = {'source_dir': mock_source_dir}


    mock_send_req.return_value = {
        "fat_report": "hello",
        "filename": mock_source_file_converted
    }

    ct_fat_measure_dcm(mock_source_dir, filepath_only=True)

    converter_call  = call(converter_payload,  converter_hostname,  converter_port,  converter_request_name)
    ct_call = call(ct_payload, ct_hostname, ct_port, ct_request_name)

    calls = [converter_call, ct_call]

    # once for converter and once for ct fat measurer
    # assert mock_send_req.call_count == 2
    mock_send_req.assert_has_calls(calls, any_order=False)


@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_lungmask_calls_container_requester_send_to_worker_once(mock_send_req):

    mock_source_dir = "/mock/source/dir"
    mock_model_name = "Mock232"

    hostname     = os.environ['LUNGMASK_HOSTNAME']
    port         = os.environ['LUNGMASK_PORT']
    request_name = 'lungmask_segment'
    payload      = {'source_dir': mock_source_dir, 'model_name': mock_model_name}

    mock_send_req.return_value = {
        "segmentation": "/seg/path",
        "input_nda": "/input/nda/path",
        "spacing": (1, 2, 3)
    }

    lungmask_segment(mock_source_dir, model_name=mock_model_name, filepath_only=True)

    mock_send_req.assert_called_once_with(payload, hostname, port, request_name)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_covid_detector_nifti_calls_container_requester_send_to_worker_once(mock_send_req):

    mock_source_file = "/mock/source/file.nii.gz"

    hostname     = os.environ["COVID_DETECTOR_HOSTNAME"]
    port         = os.environ["COVID_DETECTOR_PORT"]
    request_name = "covid_detector_nifti"
    payload      = {"source_file": mock_source_file}

    mock_send_req.return_value = {
        "lesion_detection_volume": "/rel/path/to/les_vol.nii.gz",
        "attention_volume": "/rel/path/to/attention_vol.nii.gz"
    }

    covid_detector_nifti(mock_source_file, filepath_only=True)

    mock_send_req.assert_called_once_with(payload, hostname, port, request_name)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_covid_detector_dcm_calls_container_requester_once_for_converter_and_once_for_detector(mock_send_req):
    mock_source_dir = "/mock/source/dcm_dir"
    mock_source_file_converted = "/mock/file.nii.gz"

    hostname     = os.environ["COVID_DETECTOR_HOSTNAME"]
    port         = os.environ["COVID_DETECTOR_PORT"]
    request_name = "covid_detector_nifti"
    payload      = {"source_file": mock_source_file_converted}

    converter_hostname     = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
    converter_port         = os.environ["LUNGMASK_CONVERTER_PORT"]
    converter_request_name = "lungmask_convert_dcm_to_nifti"
    converter_payload      = {'source_dir': mock_source_dir}

    mock_send_req.return_value = {
        "lesion_detection_volume": "/rel/path/to/les_vol.nii.gz",
        "attention_volume": "/rel/path/to/attention_vol.nii.gz",
        "filename": mock_source_file_converted
    }

    covid_detector_dcm(mock_source_dir, filepath_only=True)

    converter_call  = call(converter_payload,  converter_hostname,  converter_port,  converter_request_name)
    ct_call = call(payload, hostname, port, request_name)

    calls = [converter_call, ct_call]

    # once for converter and once for ct fat measurer
    # assert mock_send_req.call_count == 2
    mock_send_req.assert_has_calls(calls, any_order=False)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_covid_detector_seg_nifti_calls_container_requester_send_to_worker_once(mock_send_req):

    mock_source_file = "/mock/source/file.nii.gz"

    hostname     = os.environ["COVID_DETECTOR_SEG_HOSTNAME"]
    port         = os.environ["COVID_DETECTOR_SEG_PORT"]
    request_name = "covid_detector_seg_nifti"
    payload      = {"source_file": mock_source_file}

    mock_send_req.return_value = {
        "lesion_detection_volume": "/rel/path/to/les_vol.nii.gz",
        "attention_volume": "/rel/path/to/attention_vol.nii.gz"
    }

    covid_detector_seg_nifti(mock_source_file, filepath_only=True)

    mock_send_req.assert_called_once_with(payload, hostname, port, request_name)

@mock.patch.object(ContainerRequester, 'send_request_to_worker')
def test_covid_detector_dcm_calls_container_requester_once_for_converter_and_once_for_detector(mock_send_req):
    mock_source_dir = "/mock/source/dcm_dir"
    mock_source_file_converted = "/mock/file.nii.gz"

    hostname     = os.environ["COVID_DETECTOR_SEG_HOSTNAME"]
    port         = os.environ["COVID_DETECTOR_SEG_PORT"]
    request_name = "covid_detector_seg_nifti"
    payload      = {"source_file": mock_source_file_converted}

    converter_hostname     = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
    converter_port         = os.environ["LUNGMASK_CONVERTER_PORT"]
    converter_request_name = "lungmask_convert_dcm_to_nifti"
    converter_payload      = {'source_dir': mock_source_dir}

    mock_send_req.return_value = {
        "lesion_detection_volume": "/rel/path/to/les_vol.nii.gz",
        "attention_volume": "/rel/path/to/attention_vol.nii.gz",
        "filename": mock_source_file_converted
    }

    covid_detector_seg_dcm(mock_source_dir, filepath_only=True)

    converter_call  = call(converter_payload,  converter_hostname,  converter_port,  converter_request_name)
    ct_call = call(payload, hostname, port, request_name)

    calls = [converter_call, ct_call]

    # once for converter and once for ct fat measurer
    # assert mock_send_req.call_count == 2
    mock_send_req.assert_has_calls(calls, any_order=False)

@mock.patch.object(ContainerRequester, 'wait_until_ready')
@mock.patch('requests.get')
def test_container_requester_sends_http_request_to_worker(mock_req_get, mock_wait):
    payload = {
        "test": "payload",
        "mock": 10
    }

    worker_hostname = "test_worker_hostname"
    worker_port     = "80"
    request_name    = "test_request_name"

    mock_wait.return_value = True
    mock_req_get.return_value.text = json.dumps({"dummy": "response"})

    cont_req = ContainerRequester()
    cont_req.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

    api_address = "http://{}:{}/{}".format(worker_hostname, worker_port, request_name)
    mock_req_get.assert_called_once_with(api_address, params=payload)

@mock.patch.object(ContainerRequester, 'wait_until_ready')
@mock.patch('requests.get')
def test_container_requester_calls_wait_until_ready_once(mock_req_get, mock_wait):
    payload = {
        "test": "payload",
        "mock": 10
    }

    worker_hostname = "test_worker_hostname"
    worker_port     = "80"
    request_name    = "test_request_name"

    mock_wait.return_value = True
    mock_req_get.return_value.text = json.dumps({"dummy": "response"})

    cont_req = ContainerRequester()
    cont_req.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

    mock_wait.assert_called_once()

@mock.patch.object(ContainerRequester, 'wait_until_ready')
@mock.patch('requests.get')
def test_container_requester_throws_error_if_worker_not_ready_after_timeout(mock_req_get, mock_wait):
    payload = {
        "test": "payload",
        "mock": 10
    }

    worker_hostname = "test_worker_hostname"
    worker_port     = "80"
    request_name    = "test_request_name"

    mock_wait.return_value = False
    mock_req_get.return_value.text = json.dumps({"dummy": "response"})

    cont_req = ContainerRequester()

    try:
        cont_req.send_request_to_worker(payload, worker_hostname, worker_port, request_name)
        assert False
    except:
        pass