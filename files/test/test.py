import subprocess as sb

if __name__ == "__main__":

    print("Testing segmenter.py")
    segmenter_cmd = "pytest /app/test/test_segmenter.py"
    sb.call([segmenter_cmd], shell=True)

    print("Testing common library")
    common_lib_cmd = "pytest /app/test/test_common_lib.py"
    sb.call([common_lib_cmd], shell=True)
