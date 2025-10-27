-- database_setup.sql
CREATE SEQUENCE user_seq START WITH 51 INCREMENT BY 1;
CREATE SEQUENCE movie_seq START WITH 126 INCREMENT BY 1;
CREATE SEQUENCE review_seq START WITH 401 INCREMENT BY 1;
CREATE SEQUENCE reaction_seq START WITH 51 INCREMENT BY 1;

-- 2. USER Table (Parent Table)
CREATE TABLE "USER" (
    user_id          NUMBER PRIMARY KEY,
    username         VARCHAR2(50) UNIQUE NOT NULL,
    email            VARCHAR2(100) UNIQUE NOT NULL,
    password_hash    VARCHAR2(255) NOT NULL,
    registration_date DATE DEFAULT SYSDATE
);

-- 3. MOVIE Table (Parent Table)
CREATE TABLE MOVIE (
    movie_id         NUMBER PRIMARY KEY,
    title            VARCHAR2(255) NOT NULL,
    release_year     NUMBER(4),
    genre            VARCHAR2(100),
    director         VARCHAR2(100),
    runtime          NUMBER, -- in minutes
    poster_url       VARCHAR2(255)
);

-- 4. REVIEW Table (Child Table)
CREATE TABLE REVIEW (
    review_id        NUMBER PRIMARY KEY,
    user_id          NUMBER NOT NULL,
    movie_id         NUMBER NOT NULL,
    rating           NUMBER(2) CHECK (rating >= 1 AND rating <= 10),
    review_text      CLOB,
    review_date      DATE DEFAULT SYSDATE,
    -- Foreign Keys
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES "USER"(user_id),
    CONSTRAINT fk_review_movie FOREIGN KEY (movie_id) REFERENCES MOVIE(movie_id),
    -- Constraint for one review per user per movie (Crucial for data integrity)
    CONSTRAINT uk_user_movie_review UNIQUE (user_id, movie_id)
);

-- 5. WATCHLIST Table (Junction/Child Table)
CREATE TABLE WATCHLIST (
    user_id          NUMBER NOT NULL,
    movie_id         NUMBER NOT NULL,
    added_date       DATE DEFAULT SYSDATE,
    -- Composite Primary Key
    CONSTRAINT pk_watchlist PRIMARY KEY (user_id, movie_id),
    -- Foreign Keys
    CONSTRAINT fk_watchlist_user FOREIGN KEY (user_id) REFERENCES "USER"(user_id),
    CONSTRAINT fk_watchlist_movie FOREIGN KEY (movie_id) REFERENCES MOVIE(movie_id)
);

-- 6. REVIEW_REACTION Table
CREATE TABLE REVIEW_REACTION (
    reaction_id      NUMBER PRIMARY KEY,
    user_id          NUMBER NOT NULL,
    review_id        NUMBER NOT NULL,
    reaction_type    VARCHAR2(50) NOT NULL,
    CONSTRAINT fk_reaction_user FOREIGN KEY (user_id) REFERENCES "USER"(user_id),
    CONSTRAINT fk_reaction_review FOREIGN KEY (review_id) REFERENCES REVIEW(review_id),
    CONSTRAINT ck_reaction_type CHECK (reaction_type IN ('LIKE', 'DISLIKE', 'HELPFUL', 'FUNNY')),
    -- A user can only react once to a specific review
    CONSTRAINT uk_user_review_reaction UNIQUE (user_id, review_id)
);

-- 7. USER_PREFERENCE Table
CREATE TABLE USER_PREFERENCE (
    user_id          NUMBER NOT NULL,
    preference_type  VARCHAR2(50) NOT NULL, -- e.g., 'FAVORITE_GENRE', 'LEAST_DIRECTOR'
    preference_value VARCHAR2(255) NOT NULL,
    CONSTRAINT pk_user_preference PRIMARY KEY (user_id, preference_type),
    CONSTRAINT fk_preference_user FOREIGN KEY (user_id) REFERENCES "USER"(user_id)
);

