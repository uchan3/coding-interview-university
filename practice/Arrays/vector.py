"""
Vector (Mutable Array with Automatic Resizing)
================================================
Raw memory は ctypes.ARRAY を使って模倣する。
インデックス記法（arr[i]）は禁止し、ポインタ演算（*(ptr + i)）のみ使用。
"""

import ctypes


def _make_array(capacity: int):
    """capacity 個の int を格納できる生の配列を返す。"""
    return (ctypes.c_int * capacity)()


class Vector:
    # ─────────────────────────────────────────
    # 初期化
    # ─────────────────────────────────────────
    def __init__(self, initial_capacity: int = 0):
        """
        初期 capacity を決める。
        - initial_capacity == 0  → 16
        - それ以外                → initial_capacity 以上の最小の 2 の冪
        """
        self._capacity = self._next_power_of_2(initial_capacity) if initial_capacity > 16 else 16
        self._size = 0
        self._data = _make_array(self._capacity)  # 生配列（ポインタとして扱う）

    # ─────────────────────────────────────────
    # 公開 API
    # ─────────────────────────────────────────

    def size(self) -> int:
        """現在格納されているアイテム数を返す。"""
        return self._size

    def capacity(self) -> int:
        """確保済みのスロット数を返す。"""
        return self._capacity

    def is_empty(self) -> bool:
        """アイテムが 0 個かどうかを返す。"""
        return self._size == 0

    def at(self, index: int) -> int:
        """
        index 番目の値を返す。
        範囲外なら IndexError を raise する。

        ポインタ演算: base_ptr + index → そのアドレスの値を dereference
        """
        self._check_bounds(index)
        # *(self._data + index) に相当
        return self._deref(index)

    def push(self, item: int) -> None:
        """末尾にアイテムを追加する。capacity に達したら 2 倍に拡張。"""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        # *(ptr + size) = item
        self._write(self._size, item)
        self._size += 1

    def insert(self, index: int, item: int) -> None:
        """
        index の位置に item を挿入する。
        index 以降の要素を 1 つ右にシフトしてから書き込む。
        """
        if index < 0 or index > self._size:
            raise IndexError(f"index {index} is out of range for insert")
        if self._size == self._capacity:
            self._resize(self._capacity * 2)

        # 末尾から index まで 1 つずつ右にずらす
        # *(ptr + i) = *(ptr + i - 1) を後ろから順に
        for i in range(self._size, index, -1):
            self._write(i, self._deref(i - 1))

        self._write(index, item)
        self._size += 1

    def prepend(self, item: int) -> None:
        """先頭に挿入する（insert の index=0 の特殊ケース）。"""
        self.insert(0, item)

    def pop(self) -> int:
        """
        末尾のアイテムを取り出して返す。
        size が capacity の 1/4 になったら capacity を半分に縮小する。
        """
        if self.is_empty():
            raise IndexError("pop from empty vector")
        self._size -= 1
        value = self._deref(self._size)
        # 縮小判定（最低 16 は維持）
        if self._size > 0 and self._size <= self._capacity // 4:
            new_cap = max(16, self._capacity // 2)
            self._resize(new_cap)
        return value

    def delete(self, index: int) -> None:
        """
        index の要素を削除し、それ以降を 1 つ左にシフトする。
        """
        self._check_bounds(index)
        # index+1 から末尾まで 1 つ左にずらす
        # *(ptr + i) = *(ptr + i + 1)
        for i in range(index, self._size - 1):
            self._write(i, self._deref(i + 1))
        self._size -= 1
        if self._size > 0 and self._size <= self._capacity // 4:
            new_cap = max(16, self._capacity // 2)
            self._resize(new_cap)

    def remove(self, item: int) -> None:
        """
        item と等しい要素を全て削除する。
        後ろから走査することで、削除によるインデックスのズレを回避する。
        """
        i = self._size - 1
        while i >= 0:
            if self._deref(i) == item:
                self.delete(i)
            i -= 1

    def find(self, item: int) -> int:
        """
        item が最初に現れる index を返す。
        見つからなければ -1 を返す。
        """
        for i in range(self._size):
            if self._deref(i) == item:
                return i
        return -1

    # ─────────────────────────────────────────
    # プライベート / 内部ユーティリティ
    # ─────────────────────────────────────────

    def _resize(self, new_capacity: int) -> None:
        """
        新しい capacity の生配列を確保し、既存データをコピーして差し替える。
        これが Vector の「自動リサイズ」の核心。
        """
        new_data = _make_array(new_capacity)
        # 既存データを新配列にコピー（ポインタ演算でコピー）
        for i in range(self._size):
            # *(new_ptr + i) = *(old_ptr + i)
            ctypes.cast(new_data, ctypes.POINTER(ctypes.c_int))[i] = self._deref(i)
        self._data = new_data
        self._capacity = new_capacity

    def _deref(self, index: int) -> int:
        """*(data + index) — ポインタ演算でアドレスを計算して値を読む。"""
        ptr = ctypes.cast(self._data, ctypes.POINTER(ctypes.c_int))
        return ptr[index]  # ctypes 内部では ptr + index のアドレス計算

    def _write(self, index: int, value: int) -> None:
        """*(data + index) = value — ポインタ演算で書き込む。"""
        ptr = ctypes.cast(self._data, ctypes.POINTER(ctypes.c_int))
        ptr[index] = value

    def _check_bounds(self, index: int) -> None:
        if index < 0 or index >= self._size:
            raise IndexError(f"index {index} out of bounds (size={self._size})")

    @staticmethod
    def _next_power_of_2(n: int) -> int:
        """n 以上の最小の 2 の冪を返す。"""
        p = 16
        while p < n:
            p *= 2
        return p

    # ─────────────────────────────────────────
    # デバッグ用
    # ─────────────────────────────────────────

    def __repr__(self) -> str:
        items = [str(self._deref(i)) for i in range(self._size)]
        return f"Vector([{', '.join(items)}], size={self._size}, capacity={self._capacity})"


# ─────────────────────────────────────────────────────────────────────────────
# 動作確認
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    def section(title):
        print(f"\n{'─'*50}")
        print(f"  {title}")
        print(f"{'─'*50}")

    section("初期化")
    v = Vector()
    print(f"size()     = {v.size()}")       # 0
    print(f"capacity() = {v.capacity()}")   # 16
    print(f"is_empty() = {v.is_empty()}")   # True

    section("push × 5")
    for x in [10, 20, 30, 40, 50]:
        v.push(x)
    print(v)

    section("at(index)")
    print(f"at(0) = {v.at(0)}")  # 10
    print(f"at(2) = {v.at(2)}")  # 30
    print(f"at(4) = {v.at(4)}")  # 50
    try:
        v.at(10)
    except IndexError as e:
        print(f"at(10) → IndexError: {e}")

    section("insert(2, 99)")
    v.insert(2, 99)
    print(v)  # [10, 20, 99, 30, 40, 50]

    section("prepend(0)")
    v.prepend(0)
    print(v)  # [0, 10, 20, 99, 30, 40, 50]

    section("pop()")
    val = v.pop()
    print(f"popped: {val}")  # 50
    print(v)

    section("delete(3)")
    v.delete(3)   # 99 を削除
    print(v)      # [0, 10, 20, 30, 40]

    section("remove(20) — 全削除")
    v.push(20)
    v.push(20)
    print(f"before remove: {v}")
    v.remove(20)
    print(f"after remove:  {v}")  # 20 が全部消える

    section("find()")
    print(f"find(30) = {v.find(30)}")   # 2
    print(f"find(99) = {v.find(99)}")   # -1

    section("リサイズ確認（push で capacity 超え）")
    v2 = Vector()
    for i in range(20):
        v2.push(i)
        if v2.size() in (1, 16, 17):
            print(f"  size={v2.size()}, capacity={v2.capacity()}")

    section("リサイズ確認（pop で 1/4 以下になる）")
    v3 = Vector()
    for i in range(20):
        v3.push(i)
    print(f"before pops: size={v3.size()}, cap={v3.capacity()}")
    for _ in range(16):  # 20→4 になる
        v3.pop()
    print(f"after pops:  size={v3.size()}, cap={v3.capacity()}")

    print("\n✅ 全テスト完了")