import sprit

def test_run():
    try:
        sprit.run("sample")
        test_passed = True
    except:
        test_passed = False

    assert test_passed