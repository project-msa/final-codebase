from .polynomial import PolynomialRingDilithium

class Module:
    def __init__(self, ring):
        """
        Initialise a module over the ring ``ring``.
        """
        self.ring = ring
        self.matrix = Matrix

    def random_element(self, m, n):
        """
        Generate a random element of the module of dimension m x n

        :param int m: the number of rows in the matrix
        :param int m: the number of columns in tge matrix
        :return: an element of the module with dimension `m times n`
        """
        elements = [[self.ring.random_element() for _ in range(n)] for _ in range(m)]
        return self(elements)

    def __repr__(self):
        return f"Module over the commutative ring: {self.ring}"

    def __str__(self):
        return f"Module over the commutative ring: {self.ring}"

    def __call__(self, matrix_elements, transpose=False):
        if not isinstance(matrix_elements, list):
            raise TypeError(
                "elements of a module are matrices, built from elements of the base ring"
            )

        if isinstance(matrix_elements[0], list):
            for element_list in matrix_elements:
                if not all(isinstance(aij, self.ring.element) for aij in element_list):
                    raise TypeError(
                        f"All elements of the matrix must be elements of the ring: {self.ring}"
                    )
            return self.matrix(self, matrix_elements, transpose=transpose)

        elif isinstance(matrix_elements[0], self.ring.element):
            if not all(isinstance(aij, self.ring.element) for aij in matrix_elements):
                raise TypeError(
                    f"All elements of the matrix must be elements of the ring: {self.ring}"
                )
            return self.matrix(self, [matrix_elements], transpose=transpose)

        else:
            raise TypeError(
                "elements of a module are matrices, built from elements of the base ring"
            )

    def vector(self, elements):
        """
        Construct a vector given a list of elements of the module's ring

        :param list: a list of elements of the ring
        :return: a vector of the module
        """
        return self.matrix(self, [elements], transpose=True)


class Matrix:
    def __init__(self, parent, matrix_data, transpose=False):
        self.parent = parent
        self._data = matrix_data
        self._transpose = transpose
        if not self._check_dimensions():
            raise ValueError("Inconsistent row lengths in matrix")

    def dim(self):
        """
        Return the dimensions of the matrix with m rows
        and n columns

        :return: the dimension of the matrix ``(m, n)``
        :rtype: tuple(int, int)
        """
        if not self._transpose:
            return len(self._data), len(self._data[0])
        else:
            return len(self._data[0]), len(self._data)

    def _check_dimensions(self):
        """
        Ensure that the matrix is rectangular
        """
        return len(set(map(len, self._data))) == 1

    def transpose(self):
        """
        Return a matrix with the rows and columns of swapped
        """
        return self.parent(self._data, not self._transpose)

    def transpose_self(self):
        """
        Swap the rows and columns of the matrix in place
        """
        self._transpose = not self._transpose
        return

    T = property(transpose)

    def reduce_coefficients(self):
        """
        Reduce every element in the polynomial
        using the modulus of the PolynomialRing
        """
        for row in self._data:
            for ele in row:
                ele.reduce_coefficients()
        return self

    def __getitem__(self, idx):
        """
        matrix[i, j] returns the element on row i, column j
        """
        assert isinstance(idx, tuple) and len(idx) == 2, "Can't access individual rows"
        if not self._transpose:
            return self._data[idx[0]][idx[1]]
        else:
            return self._data[idx[1]][idx[0]]

    def __eq__(self, other):
        if self.dim() != other.dim():
            return False
        m, n = self.dim()
        return all([self[i, j] == other[i, j] for i in range(m) for j in range(n)])

    def __neg__(self):
        """
        Returns -self, by negating all elements
        """
        m, n = self.dim()
        return self.parent(
            [[-self[i, j] for j in range(n)] for i in range(m)],
            self._transpose,
        )

    def __add__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError("Can only add matrices to other matrices")
        if self.parent != other.parent:
            raise TypeError("Matrices must have the same base ring")
        if self.dim() != other.dim():
            raise ValueError("Matrices are not of the same dimensions")

        m, n = self.dim()
        return self.parent(
            [[self[i, j] + other[i, j] for j in range(n)] for i in range(m)],
            False,
        )

    def __iadd__(self, other):
        self = self + other
        return self

    def __sub__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError("Can only add matrices to other matrices")
        if self.parent != other.parent:
            raise TypeError("Matrices must have the same base ring")
        if self.dim() != other.dim():
            raise ValueError("Matrices are not of the same dimensions")

        m, n = self.dim()
        return self.parent(
            [[self[i, j] - other[i, j] for j in range(n)] for i in range(m)],
            False,
        )

    def __isub__(self, other):
        self = self - other
        return self

    def __matmul__(self, other):
        """
        Denoted A @ B
        """
        if not isinstance(other, type(self)):
            raise TypeError("Can only multiply matrcies with other matrices")
        if self.parent != other.parent:
            raise TypeError("Matrices must have the same base ring")

        m, n = self.dim()
        n_, l = other.dim()
        if not n == n_:
            raise ValueError("Matrices are of incompatible dimensions")

        return self.parent(
            [
                [sum(self[i, k] * other[k, j] for k in range(n)) for j in range(l)]
                for i in range(m)
            ]
        )

    def scale(self, other):
        """
        Multiply each element of the matrix by a polynomial or integer
        """
        if not (isinstance(other, self.parent.ring.element) or isinstance(other, int)):
            raise TypeError("Can only multiply elements with polynomials or integers")

        matrix = [[other * ele for ele in row] for row in self._data]
        return self.parent(matrix, transpose=self._transpose)

    def dot(self, other):
        """
        Compute the inner product of two vectors
        """
        if not isinstance(other, type(self)):
            raise TypeError("Can only perform dot product with other matrices")
        res = self.T @ other
        assert res.dim() == (1, 1)
        return res[0, 0]

    def __repr__(self):
        m, n = self.dim()

        if m == 1:
            return str(self._data[0])

        max_col_width = [max(len(str(self[i, j])) for i in range(m)) for j in range(n)]
        info = "]\n[".join(
            [
                ", ".join([f"{str(self[i, j]):>{max_col_width[j]}}" for j in range(n)])
                for i in range(m)
            ]
        )
        return f"[{info}]"
    
class ModuleDilithium(Module):
    def __init__(self):
        self.ring = PolynomialRingDilithium()
        self.matrix = MatrixDilithium

    def __bit_unpack(self, input_bytes, m, n, alg, packed_len, *args):
        poly_bytes = [
            input_bytes[i : i + packed_len]
            for i in range(0, len(input_bytes), packed_len)
        ]
        matrix = [
            [alg(poly_bytes[n * i + j], *args) for j in range(n)] for i in range(m)
        ]
        return self(matrix)

    def bit_unpack_t0(self, input_bytes, m, n):
        packed_len = 416
        algorithm = self.ring.bit_unpack_t0
        return self.__bit_unpack(input_bytes, m, n, algorithm, packed_len)

    def bit_unpack_t1(self, input_bytes, m, n):
        packed_len = 320
        algorithm = self.ring.bit_unpack_t1
        return self.__bit_unpack(input_bytes, m, n, algorithm, packed_len)

    def bit_unpack_s(self, input_bytes, m, n, eta):
        # Level 2 and 5 parameter set
        if eta == 2:
            packed_len = 96
        # Level 3 parameter set
        elif eta == 4:
            packed_len = 128
        else:
            raise ValueError("Expected eta to be either 2 or 4")
        algorithm = self.ring.bit_unpack_s
        return self.__bit_unpack(input_bytes, m, n, algorithm, packed_len, eta)

    def bit_unpack_w(self, input_bytes, m, n, gamma_2):
        # Level 2 parameter set
        if gamma_2 == 95232:
            packed_len = 192
        # Level 3 and 5 parameter set
        elif gamma_2 == 261888:
            packed_len = 128
        else:
            raise ValueError("Expected gamma_2 to be either (q-1)/88 or (q-1)/32")
        algorithm = self.ring.bit_unpack_w
        return self.__bit_unpack(input_bytes, m, n, algorithm, packed_len, gamma_2)

    def bit_unpack_z(self, input_bytes, m, n, gamma_1):
        # Level 2 parameter set
        if gamma_1 == (1 << 17):
            packed_len = 576
        # Level 3 and 5 parameter set
        elif gamma_1 == (1 << 19):
            packed_len = 640
        else:
            raise ValueError("Expected gamma_1 to be either 2^17 or 2^19")
        algorithm = self.ring.bit_unpack_z
        return self.__bit_unpack(input_bytes, m, n, algorithm, packed_len, gamma_1)


class MatrixDilithium(Matrix):
    def __init__(self, parent, matrix_data, transpose=False):
        super().__init__(parent, matrix_data, transpose=transpose)

    def check_norm_bound(self, bound):
        for row in self._data:
            if any(p.check_norm_bound(bound) for p in row):
                return True
        return False

    def power_2_round(self, d):
        """
        Applies `power_2_round` on every element in the
        Matrix to create two matrices.
        """
        m, n = self.dim()

        m1_elements = [[0 for _ in range(n)] for _ in range(m)]
        m0_elements = [[0 for _ in range(n)] for _ in range(m)]

        for i in range(m):
            for j in range(n):
                m1_ele, m0_ele = self[i, j].power_2_round(d)
                m1_elements[i][j] = m1_ele
                m0_elements[i][j] = m0_ele

        return self.parent(m1_elements, transpose=self._transpose), self.parent(
            m0_elements, transpose=self._transpose
        )

    def decompose(self, alpha):
        """
        Applies `power_2_round` on every element in the
        Matrix to create two matrices.
        """
        m, n = self.dim()

        m1_elements = [[0 for _ in range(n)] for _ in range(m)]
        m0_elements = [[0 for _ in range(n)] for _ in range(m)]

        for i in range(m):
            for j in range(n):
                m1_ele, m0_ele = self[i, j].decompose(alpha)
                m1_elements[i][j] = m1_ele
                m0_elements[i][j] = m0_ele

        return self.parent(m1_elements, transpose=self._transpose), self.parent(
            m0_elements, transpose=self._transpose
        )

    def __bit_pack(self, algorithm, *args):
        return b"".join(algorithm(poly, *args) for row in self._data for poly in row)

    def bit_pack_t1(self):
        algorithm = self.parent.ring.element.bit_pack_t1
        return self.__bit_pack(algorithm)

    def bit_pack_t0(self):
        algorithm = self.parent.ring.element.bit_pack_t0
        return self.__bit_pack(algorithm)

    def bit_pack_s(self, eta):
        algorithm = self.parent.ring.element.bit_pack_s
        return self.__bit_pack(algorithm, eta)

    def bit_pack_w(self, gamma_2):
        algorithm = self.parent.ring.element.bit_pack_w
        return self.__bit_pack(algorithm, gamma_2)

    def bit_pack_z(self, gamma_1):
        algorithm = self.parent.ring.element.bit_pack_z
        return self.__bit_pack(algorithm, gamma_1)

    def to_ntt(self):
        """
        Convert every element of the matrix into NTT form
        """
        data = [[x.to_ntt() for x in row] for row in self._data]
        return self.parent(data, transpose=self._transpose)

    def from_ntt(self):
        """
        Convert every element of the matrix from NTT form
        """
        data = [[x.from_ntt() for x in row] for row in self._data]
        return self.parent(data, transpose=self._transpose)

    def high_bits(self, alpha, is_ntt=False):
        matrix = [
            [ele.high_bits(alpha, is_ntt=is_ntt) for ele in row] for row in self._data
        ]
        return self.parent(matrix)

    def low_bits(self, alpha, is_ntt=False):
        matrix = [
            [ele.low_bits(alpha, is_ntt=is_ntt) for ele in row] for row in self._data
        ]
        return self.parent(matrix)

    def make_hint(self, other, alpha):
        """
        Figure 3 (Supporting algorithms for Dilithium)
        https://pq-crystals.org/dilithium/data/dilithium-specification-round3-20210208.pdf
        """
        matrix = [
            [p.make_hint(q, alpha) for p, q in zip(r1, r2)]
            for r1, r2 in zip(self._data, other._data)
        ]
        return self.parent(matrix)

    def make_hint_optimised(self, other, alpha):
        """
        Figure 3 (Supporting algorithms for Dilithium)
        https://pq-crystals.org/dilithium/data/dilithium-specification-round3-20210208.pdf
        """
        matrix = [
            [p.make_hint_optimised(q, alpha) for p, q in zip(r1, r2)]
            for r1, r2 in zip(self._data, other._data)
        ]
        return self.parent(matrix)

    def use_hint(self, other, alpha):
        """
        Figure 3 (Supporting algorithms for Dilithium)
        https://pq-crystals.org/dilithium/data/dilithium-specification-round3-20210208.pdf
        """
        matrix = [
            [p.use_hint(q, alpha) for p, q in zip(r1, r2)]
            for r1, r2 in zip(self._data, other._data)
        ]
        return self.parent(matrix)

    def sum_hint(self):
        """
        Helper function to count the number of coeffs == 1
        in all the polynomials of a matrix
        """
        return sum(c for row in self._data for p in row for c in p)