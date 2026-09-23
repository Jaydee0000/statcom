# Database Design

## Players

Stores long-term player information

- id
- first_name
- last_name
- dob
- position
- secondary position
- team_id
- jersey_number
- height
- weight
- created_at


## PlayerMatchStats

Store specific player stats on a given match

- id
- player_id
- match_id
- minutes_played
- goals
- assists
- passes_completed
- progressive_passes
- tackles
- interceptions
- turnovers
.... I need to talk to the coach and see what all we want to take into consideration

## Teams

- id
- name
- short_name
- city
- state
- age_group
- level


## Match

Store the outcomes and superficial information about a match

- match_id
- weather
- Date_of_match
- location
- time
- home_team_id
- away_team_id
- home_score
- away_score
- status
- competition
- season


## Log In

stores the login of a user 

- user_id
- password
- time_of_registration
- email
- role
- last_login_at
- is_active


## Videos

store video information

- id
- match_id
- file_url
- filename
- duration_seconds
- uploaded_by
- uploaded_at


## annotations

where i store annotations for a given match

- id
- match_id
- video_id
- player_id
- created_by
- timestamp_seconds
- event_type
- outcome
- notes
- gameplan_adherence
- created_at
- updated_at


