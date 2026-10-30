from feedbacklab.pii import scrub


def test_phone_formats():
    for raw in [
        "hubungi 081234567890",
        "wa +62 812-3456-7890",
        "telp 0812.3456.789",
        "62812 3456 7890",
    ]:
        out = scrub(raw)
        assert "[TELEPON]" in out.text, raw
        assert out.counts == {"phone": 1}


def test_email_url_mention():
    out = scrub("kirim ke budi.s@mail.co.id atau cek https://toko.id/x?a=1 dan @cs_toko")
    assert out.text == "kirim ke [EMAIL] atau cek [URL] dan [AKUN]"
    assert out.counts == {"url": 1, "email": 1, "mention": 1}


def test_long_numbers_but_not_prices_or_years():
    out = scrub("NIK 3201234567890001, harga 150000, tahun 2023, 4G")
    assert out.text == "NIK [NOMOR], harga 150000, tahun 2023, 4G"
    assert out.counts == {"long_number": 1}


def test_clean_text_untouched():
    t = "Makanannya enak, pelayanan 10/10!"
    assert scrub(t).text == t
    assert scrub(t).counts == {}


def test_email_not_counted_as_mention():
    out = scrub("email andi@gmail.com")
    assert out.counts == {"email": 1}
