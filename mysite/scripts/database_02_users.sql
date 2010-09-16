CREATE USER 'oh_milestone_a'@'localhost' IDENTIFIED BY 'ahmaC0Th';  -- so that the account has a password
GRANT ALL ON oh_milestone_a.* TO 'oh_milestone_a'@'localhost';      -- so that ./bin/mysite has a database
GRANT ALL ON test_oh_milestone_a.* TO 'oh_milestone_a'@'localhost'; -- for the test suite

