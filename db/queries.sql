-- The main queries the app runs (server/posts.py), written with T-SQL variables
-- so you can run them in VS Code against wjford_myapp and compare with the page.
-- In Python the @variables are ? parameters; user input is never pasted into SQL.

-- 1. Feed / search: newest posts whose caption or author matches a search term.
DECLARE @search NVARCHAR(100) = N'light';
DECLARE @viewer INT = 1;          -- logged-in user (0 = nobody), for "liked by me"
DECLARE @pattern NVARCHAR(102) = N'%' + @search + N'%';

SELECT TOP (12)
    p.PostID, p.Caption, p.CreatedAt,
    u.Username, u.DisplayName,
    (SELECT COUNT(*) FROM Likes l WHERE l.PostID = p.PostID) AS LikeCount,
    (SELECT COUNT(*) FROM Comments c WHERE c.PostID = p.PostID AND c.IsDeleted = 0) AS CommentCount,
    CASE WHEN EXISTS (SELECT 1 FROM Likes l WHERE l.PostID = p.PostID AND l.UserID = @viewer)
         THEN 1 ELSE 0 END AS LikedByMe
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
WHERE p.Caption LIKE @pattern OR u.Username LIKE @pattern OR u.DisplayName LIKE @pattern
ORDER BY p.PostID DESC;

-- 2. One photographer's posts.
DECLARE @username NVARCHAR(30) = N'mara_lens';

SELECT p.PostID, p.Caption, p.CreatedAt, COUNT(ph.PhotoID) AS PhotoCount
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
LEFT JOIN Photos ph ON ph.PostID = p.PostID
WHERE u.Username = @username
GROUP BY p.PostID, p.Caption, p.CreatedAt
ORDER BY p.PostID DESC;

-- 3. A post's comment thread (ParentCommentID links replies to their parent).
DECLARE @post INT = 1;

WITH Thread AS (
    SELECT c.CommentID, c.ParentCommentID, c.Body, c.UserID, c.CreatedAt, 0 AS Depth,
           CAST(RIGHT('0000000000' + CAST(c.CommentID AS VARCHAR(10)), 10) AS VARCHAR(400)) AS SortPath
    FROM Comments c
    WHERE c.PostID = @post AND c.ParentCommentID IS NULL
    UNION ALL
    SELECT c.CommentID, c.ParentCommentID, c.Body, c.UserID, c.CreatedAt, t.Depth + 1,
           CAST(t.SortPath + '/' + RIGHT('0000000000' + CAST(c.CommentID AS VARCHAR(10)), 10) AS VARCHAR(400))
    FROM Comments c
    JOIN Thread t ON c.ParentCommentID = t.CommentID
)
SELECT REPLICATE('    ', t.Depth) + u.Username AS Author, t.Body, t.CreatedAt
FROM Thread t
JOIN Users u ON u.UserID = t.UserID
ORDER BY t.SortPath;

-- 4. Most-liked photographers.
SELECT TOP (5) u.Username, COUNT(l.PostID) AS LikesReceived
FROM Users u
JOIN Posts p ON p.UserID = u.UserID
LEFT JOIN Likes l ON l.PostID = p.PostID
GROUP BY u.Username
ORDER BY LikesReceived DESC;
