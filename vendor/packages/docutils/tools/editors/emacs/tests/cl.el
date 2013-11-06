;; Tests for replacement functions for `cl.el'

(add-to-list 'load-path ".")
(load "init" nil t)
(init-rst-ert nil)

(ert-deftest rst-signum ()
  "Test `rst-signum'."
  (should (equal (rst-signum 10) 1))
  (should (equal (rst-signum -10) -1))
  (should (equal (rst-signum 0) 0))
  )

(ert-deftest rst-some ()
  "Test `rst-some'."
  (should (equal (rst-some nil) nil))
  (should (equal (rst-some '(t)) t))
  (should (equal (rst-some '(0)) 0))
  (should (equal (rst-some '(1)) 1))
  (should (equal (rst-some '(nil 1)) 1))
  (should (equal (rst-some '(nil nil)) nil))
  (should (equal (rst-some nil 'not) nil))
  (should (equal (rst-some '(t) 'not) nil))
  (should (equal (rst-some '(0) 'not) nil))
  (should (equal (rst-some '(1 nil) 'not) t))
  (should (equal (rst-some '(nil 1) 'not) t))
  (should (equal (rst-some '(nil nil) 'not) t))
  )

(ert-deftest rst-position ()
  "Test `rst-position'."
  (should (equal (rst-position nil nil) nil))
  (should (equal (rst-position t '(nil)) nil))
  (should (equal (rst-position nil '(t)) nil))
  (should (equal (rst-position nil '(nil)) 0))
  (should (equal (rst-position t '(t)) 0))
  (should (equal (rst-position t '(nil t)) 1))
  (should (equal (rst-position t '(nil t t nil sym)) 1))
  (should (equal (rst-position t '(nil (t) t nil sym)) 2))
  (should (equal (rst-position 'sym '(nil (t) t nil sym)) 4))
  (should (equal (rst-position 'sym '(nil (t) t nil t)) nil))
  (should (equal (rst-position '(t) '(nil (t) t nil sym)) 1))
  (should (equal (rst-position '(1 2 3) '(nil (t) t nil sym)) nil))
  (should (equal (rst-position '(1 2 3) '(nil (t) t (1 2 3) t)) 3))
  (should (equal (rst-position '(1 2 3) '(nil (t) t (1 2 3) (1 2 3))) 3))
  )

(ert-deftest rst-position-if ()
  "Test `rst-position-if'."
  (should (equal (rst-position-if 'not '(t nil nil)) 1))

  (should (equal (rst-position-if 'not nil) nil))
  (should (equal (rst-position-if 'identity '(nil)) nil))
  (should (equal (rst-position-if 'not '(t)) nil))
  (should (equal (rst-position-if 'not '(nil)) 0))
  (should (equal (rst-position-if 'not '(nil nil)) 0))
  (should (equal (rst-position-if 'not '(t t nil)) 2))
  )
