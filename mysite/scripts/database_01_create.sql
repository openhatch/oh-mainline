CREATE DATABASE oh_milestone_a DEFAULT CHARACTER SET = utf8;          -- so there is somewhere to store the data
GRANT ALL ON oh_milestone_a.* TO 'oh_milestone_a'@'localhost' IDENTIFIED BY 'ahmaC0Th'; -- so that ./bin/mysite has a database
GRANT ALL ON test_oh_milestone_a.* TO 'oh_milestone_a'@'localhost'; -- for the test suite
