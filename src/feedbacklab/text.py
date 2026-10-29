"""Normalisasi teks yang sengaja sederhana supaya bisa ditiru persis oleh JavaScript di browser."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Huruf kecil, semua selain a-z dan 0-9 menjadi satu spasi. Token [URL] dan sejenisnya
    hasil penghapusan data pribadi ikut menjadi kata biasa (url, email, akun, telepon, nomor)."""
    return _NON_ALNUM.sub(" ", text.lower()).strip()


def tokens(text: str) -> list[str]:
    """Kata dengan panjang minimal 2 huruf, sama dengan token_pattern bawaan scikit-learn."""
    return [t for t in normalize(text).split(" ") if len(t) >= 2]


# Daftar kata henti bahasa Indonesia untuk topic modeling saja (klasifikasi sentimen tidak
# membuang kata henti karena kata seperti "tidak" dan "kurang" membawa sentimen).
# Disusun manual: kata fungsi, kata ganti, kata bantu, dan bentuk tidak baku yang umum.
STOPWORDS = frozenset(
    """
    ada adalah adanya agak agar akan akhirnya aku akulah amat amatlah anda andalah antar antara
    apa apaan apabila apakah apalagi atas atau ataupun bagai bagaimana bagi bagian bahkan bahwa
    baik bakal banget banyak barangkali baru bawah beberapa begini begitu belum benar berada
    berapa berbagai berikut bersama betul biar biasa biasanya bila bisa boleh bukan bukankah
    cuma cukup dahulu dalam dan dapat dari daripada datang dekat demi dengan depan di dia
    diri dirinya disini disana dong dulu enggak engga entah gak ga gimana gitu hal hampir
    hanya harus hingga ia ialah ini inilah itu itulah jadi jangan jika jikalau juga jika kah
    kala kalau kali kalian kami kamu kan kapan karena kata ke kebanyakan kecil kembali kenapa
    kepada ketika kini kita kok krn lagi lah lain lalu lama lebih lewat maka makin malah mana
    masih mau melalui memang mereka meski mungkin nah namun nanti nya nyaa oleh pada padahal
    para pernah pun punya saat saja sambil sampai sangat saya se sebab sebagai sebelum sebuah
    secara sedang sedikit segala sehingga sejak sekali sekarang selain selalu seluruh semua
    sendiri seperti serta sering sesuatu setelah setiap siapa sih suatu sudah supaya tadi tak
    tanpa tapi tentang terhadap terlalu termasuk tetap tetapi tidak tiap toh tuh untuk waktu
    ya yaitu yakni yang yg dgn utk tdk sdh aja udah udh bgt gk tp jd dr klo kalo deh nih
    the and of to is in for it
    """.split()
)
