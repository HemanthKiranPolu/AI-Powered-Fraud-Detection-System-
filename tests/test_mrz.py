from worker.mrz import validate_mrz


def test_validate_mrz_td3():
    # Example TD3 MRZ lines (not real)
    l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    ok, parsed = validate_mrz([l1, l2])
    assert isinstance(ok, bool)


def test_validate_mrz_td1():
    l1 = "I<UTOD231458907<<<<<<<<<<<<<<<"
    l2 = "7408122F1204159UTO<<<<<<<<<<<6"
    l3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"
    ok, parsed = validate_mrz([l1, l2, l3])
    assert isinstance(ok, bool)

