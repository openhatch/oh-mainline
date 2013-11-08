
CREATE TRIGGER delete_from_zoho AFTER DELETE ON profile_person FOR EACH ROW
BEGIN
    INSERT INTO profile_people_to_remove_from_zoho (zoho_id) VALUES (old.zoho_id);
END;
