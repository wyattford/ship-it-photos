-- Photo-sharing app schema (SQL Server / T-SQL). Run against wjford_myapp.
-- db/seed.py runs this file (it drops and recreates every table).
-- Deletes are done explicitly in the app (no ON DELETE CASCADE) to avoid
-- SQL Server's "multiple cascade paths" restriction.

DROP TABLE IF EXISTS Likes;
DROP TABLE IF EXISTS Comments;
DROP TABLE IF EXISTS Photos;
DROP TABLE IF EXISTS Posts;
DROP TABLE IF EXISTS Sessions;
DROP TABLE IF EXISTS Users;
GO

CREATE TABLE Users (
    UserID        INT IDENTITY(1,1) PRIMARY KEY,
    Username      NVARCHAR(30)  NOT NULL CONSTRAINT UQ_Users_Username UNIQUE,
    DisplayName   NVARCHAR(60)  NOT NULL,
    PasswordHash  NVARCHAR(200) NOT NULL,
    Bio           NVARCHAR(300) NULL,
    CreatedAt     DATETIME2(0)  NOT NULL CONSTRAINT DF_Users_CreatedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE Sessions (
    Token      CHAR(64)     NOT NULL PRIMARY KEY,   -- random hex, sent as an HttpOnly cookie
    UserID     INT          NOT NULL CONSTRAINT FK_Sessions_Users REFERENCES Users(UserID),
    CreatedAt  DATETIME2(0) NOT NULL CONSTRAINT DF_Sessions_CreatedAt DEFAULT SYSUTCDATETIME(),
    ExpiresAt  DATETIME2(0) NOT NULL
);

CREATE TABLE Posts (
    PostID     INT IDENTITY(1,1) PRIMARY KEY,
    UserID     INT            NOT NULL CONSTRAINT FK_Posts_Users REFERENCES Users(UserID),
    Caption    NVARCHAR(2000) NOT NULL CONSTRAINT DF_Posts_Caption DEFAULT N'',
    CreatedAt  DATETIME2(0)   NOT NULL CONSTRAINT DF_Posts_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt  DATETIME2(0)   NULL
);
CREATE INDEX IX_Posts_UserID ON Posts(UserID);

CREATE TABLE Photos (
    PhotoID    INT IDENTITY(1,1) PRIMARY KEY,
    PostID     INT           NOT NULL CONSTRAINT FK_Photos_Posts REFERENCES Posts(PostID),
    SortOrder  TINYINT       NOT NULL,              -- 0..9, order within the post
    FilePath   NVARCHAR(260) NOT NULL,              -- relative to uploads/, e.g. ab12.jpg
    ThumbPath  NVARCHAR(260) NOT NULL,              -- relative to uploads/, e.g. thumbs/ab12.webp
    Width      INT           NOT NULL,
    Height     INT           NOT NULL,
    CONSTRAINT UQ_Photos_Post_Order UNIQUE (PostID, SortOrder),
    CONSTRAINT CK_Photos_SortOrder CHECK (SortOrder BETWEEN 0 AND 9)
);

CREATE TABLE Comments (
    CommentID        INT IDENTITY(1,1) PRIMARY KEY,
    PostID           INT            NOT NULL CONSTRAINT FK_Comments_Posts REFERENCES Posts(PostID),
    UserID           INT            NOT NULL CONSTRAINT FK_Comments_Users REFERENCES Users(UserID),
    ParentCommentID  INT            NULL     CONSTRAINT FK_Comments_Parent REFERENCES Comments(CommentID),
    Body             NVARCHAR(2000) NOT NULL,
    IsDeleted        BIT            NOT NULL CONSTRAINT DF_Comments_IsDeleted DEFAULT 0,  -- soft delete keeps replies attached
    CreatedAt        DATETIME2(0)   NOT NULL CONSTRAINT DF_Comments_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt        DATETIME2(0)   NULL
);
CREATE INDEX IX_Comments_PostID ON Comments(PostID);

CREATE TABLE Likes (
    UserID     INT          NOT NULL CONSTRAINT FK_Likes_Users REFERENCES Users(UserID),
    PostID     INT          NOT NULL CONSTRAINT FK_Likes_Posts REFERENCES Posts(PostID),
    CreatedAt  DATETIME2(0) NOT NULL CONSTRAINT DF_Likes_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_Likes PRIMARY KEY (UserID, PostID)  -- one like per user per post
);
CREATE INDEX IX_Likes_PostID ON Likes(PostID);
GO
