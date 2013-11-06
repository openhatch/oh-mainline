;; Tests for operations on list items

(add-to-list 'load-path ".")
(load "init" nil t)
(init-rst-ert t)

(ert-deftest items-asserts ()
  "Check some assertions."
  (should (equal ert-Buf-point-char "\^@"))
  (should (equal ert-Buf-mark-char "\^?"))
  )

(ert-deftest rst-convert-bullets-to-enumeration ()
  "Tests `rst-convert-bullets-to-enumeration'."
  (should (ert-equal-buffer
	   (rst-convert-bullets-to-enumeration)
"\^@Normal paragraph.

* A bullet

* Another bullet

Another normal paragraph.

\^?"
"\^@Normal paragraph.

1. A bullet

2. Another bullet

Another normal paragraph.

\^?" t))
  (should (ert-equal-buffer
	   (rst-convert-bullets-to-enumeration)
"Normal paragraph.

\^?* A bullet

* Another bullet

\^@Another normal paragraph.

"
"Normal paragraph.

\^?1. A bullet

2. Another bullet

\^@Another normal paragraph.

" t))
  (should (ert-equal-buffer
	   (rst-convert-bullets-to-enumeration)
"Normal paragraph.

\^?* A bullet

* Another bullet

1. A bullet

2. Another bullet

\^@Another normal paragraph.

"
		      
"Normal paragraph.

\^?1. A bullet

2. Another bullet

3. A bullet

4. Another bullet

\^@Another normal paragraph.

" t))
  )

(ert-deftest rst-convert-bullets-to-enumeration-BUGS ()
  "Exposes bugs in `rst-convert-bullets-to-enumeration'."
  :expected-result :failed ;; These are bugs
  (should (ert-equal-buffer
	   (rst-convert-bullets-to-enumeration)
"\^@Normal paragraph.

* A bullet

* Another bullet

  * A bullet

  * Another bullet

Another normal paragraph.

\^?"
"\^@Normal paragraph.

1. A bullet

2. Another bullet

  * A bullet

  * Another bullet

Another normal paragraph.

\^?" t))
  )

(ert-deftest rst-insert-list-continue ()
  "Tests `rst-insert-list' when continuing a list."
  (should (ert-equal-buffer
	   (rst-insert-list)
"* Some text\^@\n"
"* Some text
* \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"* Some \^@text\n"
"* Some text
* \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"* \^@Some text\n"
"* Some text
* \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"* Some text
  - A deeper hyphen bullet\^@\n"
"* Some text
  - A deeper hyphen bullet
  - \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"* Some text
  - \^@Some text\n"
"* Some text
  - Some text
  - \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"1. Some text\^@\n"
"1. Some text
2. \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"2. Some text\^@\n"
"2. Some text
3. \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"a) Some text\^@\n"
"a) Some text
b) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"(A) Some text\^@\n"
"(A) Some text
\(B) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"(I) Some text\^@\n"
"(I) Some text
\(J) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"(I) Some text\^@\n"
"(I) Some text
\(J) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"(h) Some text
\(i) Some text\^@\n"
"(h) Some text
\(i) Some text
\(j) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list t)
"(i) Some text\^@\n"
"(i) Some text
\(ii) \^@\n"))
  (should (ert-equal-buffer
	   (rst-insert-list)
"(iv) Some text
\(v) Some text\^@\n"
"(iv) Some text
\(v) Some text
\(vi) \^@\n"))
  )

(ert-deftest rst-insert-list-continue-BUGS ()
  "Exposes bugs in `rst-insert-list-continue'."
  :expected-result :failed ;; These are bugs
  (should (ert-equal-buffer
	   (rst-insert-list)
"(iv) Some text

\(v) Some text\^@\n"
"(iv) Some text

\(v) Some text
\(vi) \^@\n")))

(ert-deftest rst-insert-list-new ()
  "Tests `rst-insert-list' when inserting a new list."
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"* \^@\n" '("*")))
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"- \^@\n" '("-")))
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"#. \^@\n" '("#.")))
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"5) \^@\n" '("1)" 5)))
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"(i) \^@\n" '("(i)" "")))
  (should (ert-equal-buffer
	   (rst-insert-list)
"\^@\n"
"IV. \^@\n" '("I." 4)))
  (should (ert-equal-buffer
	   (rst-insert-list)
"Some line\^@\n"
"Some line

IV. \^@\n" '("I." 4)))
  (should (ert-equal-buffer
	   (rst-insert-list)
"Some line
\^@\n"
"Some line

IV. \^@\n" '("I." 4)))
  (should (ert-equal-buffer
	   (rst-insert-list)
"Some line

\^@\n"
"Some line

IV. \^@\n" '("I." 4)))
  )
