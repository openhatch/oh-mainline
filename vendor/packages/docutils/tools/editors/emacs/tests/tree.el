;; Tests for `rst-section-tree'

(add-to-list 'load-path ".")
(load "init" nil t)
(init-rst-ert t)

(ert-deftest toc-asserts ()
  "Check some assertions."
  (should (equal ert-Buf-point-char "\^@"))
  (should (equal ert-Buf-mark-char "\^?"))
  )

(defun mrk2int (obj)
  "Replace all markers in OBJ by integers and return result."
  (cond
   ((markerp obj)
    (marker-position obj))
   ((stringp obj)
    obj)
   ((sequencep obj)
    (mapcar 'mrk2int obj))
   (t obj)))

(defun section-tree ()
  "Return result of `rst-section-tree' with markers replaced by integers."
  (mrk2int (rst-section-tree)))

(defun section-tree-point ()
  "Return result of `rst-section-tree-point' with markers replaced by integers."
  (mrk2int (rst-section-tree-point (rst-section-tree))))

(ert-deftest rst-section-tree ()
  "Tests `rst-section-tree'."
  (let ((title "=====
Title
=====

")
	(headers "Header A
========

Header B
========

Subheader B.a
-------------

SubSubheader B.a.1
~~~~~~~~~~~~~~~~~~

Subheader B.b
-------------

Header C
========"))
    (should (ert-equal-buffer-return
	     (section-tree)
	     ""
	     t
	     '((nil))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree)
	     title
	     t
	     '((nil 7) (("Title" 7)))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree)
	     (concat title headers)
	     t
	     '((nil 7)
	       (("Title" 7)
		(("Header A" 20))
		(("Header B" 39)
		 (("Subheader B.a" 58)
		  (("SubSubheader B.a.1" 87)))
		 (("Subheader B.b" 126)))
		(("Header C" 155))))
	     ))
    ))

(ert-deftest rst-section-tree-point ()
  "Tests `rst-section-tree-point'."
  (let ((title "=====
Title
=====

"))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     "\^@"
	     t
	     '(((nil)))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat "\^@" title)
	     t
	     '(((nil 7)))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat title "\^@")
	     t
	     '(((nil 7) ("Title" 7)) ("Title" 7))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat title "\^@Header A
========

Header B
========

Subheader B.a
-------------

SubSubheader B.a.1
~~~~~~~~~~~~~~~~~~

Subheader B.b
-------------

Header C
========")
	     t
	     '(((nil 7) ("Title" 7) ("Header A" 20)) ("Header A" 20))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat title "Header A
========

Header B
========
\^@
Subheader B.a
-------------

SubSubheader B.a.1
~~~~~~~~~~~~~~~~~~

Subheader B.b
-------------

Header C
========")
	     t
	     '(((nil 7) ("Title" 7) ("Header B" 39)) ("Header B" 39)
	       (("Subheader B.a" 58)
		(("SubSubheader B.a.1" 87)))
	       (("Subheader B.b" 126)))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat title "Header A
========

Header B
========

Subheader B.a\^@
-------------

SubSubheader B.a.1
~~~~~~~~~~~~~~~~~~

Subheader B.b
-------------

Header C
========")
	     t
	     '(((nil 7) ("Title" 7) ("Header B" 39) ("Subheader B.a" 58))
	       ("Subheader B.a" 58)
	       (("SubSubheader B.a.1" 87)))
	     ))
    (should (ert-equal-buffer-return
	     (section-tree-point)
	     (concat title "Header A
========

Header B
========

Subheader B.a
-------------

SubSubheader B.a.1
~~~~~~~~~~~~~~~~~~

S\^@ubheader B.b
-------------

Header C
========")
	     t
	     '(((nil 7) ("Title" 7) ("Header B" 39) ("Subheader B.b" 126))
	       ("Subheader B.b" 126))
	     ))
    ))
