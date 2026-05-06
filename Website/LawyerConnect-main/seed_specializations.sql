USE LawyerConnectDB;
GO

IF NOT EXISTS (SELECT 1 FROM Specializations)
BEGIN
    INSERT INTO Specializations (Name, Description) VALUES
    ('Corporate Law', 'Deals with the formation and operations of corporations'),
    ('Criminal Law', 'Focuses on behaviors that are sanctioned under criminal code'),
    ('Family Law', 'Deals with matters relating to family and domestic relations'),
    ('Intellectual Property', 'Secures and enforces legal rights to inventions, designs, and artwork'),
    ('Real Estate', 'Involves land, property, and associated structures'),
    ('Immigration Law', 'Involves the legal issues of navigating the immigration process');
    PRINT 'Specializations seeded successfully.'
END
ELSE
BEGIN
    PRINT 'Specializations already exist.'
END
GO
