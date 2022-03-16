/*PRAGMA foreign_keys=OFF;*/
BEGIN TRANSACTION;
CREATE TABLE "user" (
	id SERIAL NOT NULL PRIMARY KEY, 
	public_id VARCHAR(50) NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(75) NOT NULL, 
	password VARCHAR(60) NOT NULL, 
	date_joined TIMESTAMP, 
	UNIQUE (username), 
	UNIQUE (email)
);

CREATE UNIQUE INDEX ix_user_public_id ON "user" (public_id);
CREATE UNIQUE INDEX ix_user_email ON "user" (email);


/*Insert row, sync the primary key*/
INSERT INTO "user" VALUES(1,'9edcf16e-9391-4096-ab3f-a8b2017e64f8','testing','testing@gmail.com','$2b$12$k.HNKyENLhodcyqUBu5XteuKOlNmQLrcsWoy45prpC/kb8zSFOwJS','2022-01-21 03:29:10.899459');
SELECT setval('user_id_seq', (SELECT MAX(id) FROM "user"));

COMMIT;
