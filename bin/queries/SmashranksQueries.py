import smashggpy.queries.Schema as schema

schema.user_schema = """
id
name
slug
birthday
genderPronoun
player {{
  {0}
}}
location {{
  {1}
}}
authorizations(types: {2}){{
  {3}
}}
images {{
  id
  type
  url
  height
  width
}}
""".format(schema.player_schema, schema.location_schema, schema.authorization_types, schema.authorization_schema)

schema.attendee_schema = """
id
gamerTag
prefix
checkedInAt
verified
connectedAccounts
contactInfo{{
    {0}
}}
user {{
  {1}
}}
events{{
    id
}}
""".format(schema.attendee_contact_info_schema, schema.user_schema)

schema.entrant_schema = """
id
name
event {{
  id
  name
  }}
skill
participants{{
    {0}
}}
""".format(schema.attendee_schema)

schema.gg_set_schema = """
id
displayScore
fullRoundText
round
startedAt
completedAt
winnerId
wPlacement
lPlacement
setGamesType
totalGames
state
identifier
vodUrl
hasPlaceholder
event {{
  id
  name
}}
phaseGroup {{
  id
  displayIdentifier
}}
slots(includeByes: true){{
    {0}
}}
games {{
  id
  orderNum
  state
  winnerId
  stage {{
    id
    name
  }}
  selections {{
    id
    entrant {{
      id
      name
      }}
    orderNum
    selectionValue
    selectionType
  }}
}}
""".format(schema.gg_set_slot_schema)

get_tournament = """
query TournamentQuery($id: ID!){{
    tournament(id: $id){{
        {0}
        shortSlug
    }}
}}
""".format(schema.tournament_schema)

get_tournament_by_slug = """
query TournamentQuery($slug: String){{
    tournament(slug: $slug){{
        {0}
    }}
}}
""".format(schema.tournament_schema)


get_tournament_events = """
query TournamentEvents($id: ID!){{
    tournament(id: $id){{
        events{{
            {0}
        }}
    }}
}}
""".format(schema.event_schema)

get_tournament_phases = """
query TournamentPhases($id: ID!){{
    tournament(id: $id){{
        events{{
            phases{{
                {0}
                isExhibition
            }}
        }}
    }}
}}
""".format(schema.phase_schema)

get_tournament_phase_groups = """
query TournamentPhaseGroups($id: ID!){{
    tournament(id: $id){{
        events{{
            phaseGroups{{
                {0}
            }}
        }}
    }}
}}
""".format(schema.phase_group_schema)

get_event_phases = """
query EventPhases($id: ID!){{
    event(id: $id){{
        phases{{
            {0}
            isExhibition
            phaseOrder
        }}
    }}
}}
""".format(schema.phase_schema)

get_event_phase_groups = """
query EventPhaseGroups($id: ID!){{
    event(id: $id){{
        phaseGroups{{
            {0}
            progressionsOut {{
              id
              originOrder
              originPhaseGroup {{
                id
              }}
              originPlacement
            }}
            rounds {{
              id
              bestOf
              number
            }}
        }}
    }}
}}
""".format(schema.phase_group_schema)

phase_phase_groups = """
query PhasePhaseGroups($id: ID!, $page: Int, $perPage: Int, $sortBy: String, $entrantIds: [ID], $filter: PhaseGroupPageQueryFilter){{
   phase(id: $id){{
        phaseGroups(query: {{
            page: $page,
            perPage: $perPage,
            sortBy: $sortBy,
            entrantIds: $entrantIds,
            filter: $filter
        }})
        {{
            pageInfo{{
                totalPages
            }}
            nodes{{
                {0}
                progressionsOut {{
                  id
                  originOrder
                  originPhaseGroup {{
                    id
                  }}
                  originPlacement
                }}
                rounds {{
                  id
                  bestOf
                  number
                }}
            }}  
        }}
    }}
}}
""".format(schema.phase_group_schema)

phase_group_entrants = """
query PhaseGroupEntrants($id: ID!, $page: Int, $perPage: Int, $sortBy: String, $filter: SeedPageFilter){{
    phaseGroup(id: $id){{
        paginatedSeeds(
            query: {{
                page: $page,
                perPage: $perPage,
                sortBy: $sortBy,
                filter: $filter
            }}
        )
        {{
            pageInfo{{
                totalPages
            }}
            nodes{{
              id
              placement
              seedNum
              isBye
              entrant{{
                  {0}
              }}
            }}
        }}
    }}
}}
""".format(schema.entrant_schema)

phase_group_sets = """
query PhaseGroupEntrants($id: ID!, $page: Int, $perPage: Int, $sortType: SetSortType, $filters: SetFilters){{
    phaseGroup(id: $id){{
        paginatedSets(page:$page, perPage:$perPage, sortType:$sortType, filters:$filters){{
            pageInfo{{
                totalPages
            }}
            nodes{{
                {0}
            }}
        }}
    }}
}}
""".format(schema.gg_set_schema)

SR_tournament_query = """
query TournamentQuery($slug: String) {
		tournament(slug: $slug){
			id
			name
      slug
      shortSlug
      city
      postalCode
      addrState
      countryCode
      venueAddress
      venueName
      lat
      lng
      timezone
      startAt
      endAt
    	hashtag
      isOnline
    	images{
        id
        type
        url
        height
        width
      }
      owner {
        id
        name
        player{
          id
          gamerTag
        }
      }
			events {
				id
				name
			}
		}
	}
"""


SR_user_query = """
query UserInfo {
  player($id: ID!) {
    id
    user {
      id
      bio
      birthday
      genderPronoun
      name
      slug
      authorizations(types: [TWITTER, TWITCH, DISCORD, MIXER]) {
        id
        externalUsername
        stream {
          id
          isOnline
          name
          type
        }
        type
        url
      }
      location {
        id
        city
        country
        countryId
        state
        stateId
      }
      player {
        gamerTag
        prefix
        rankings(limit: 5, videogameId: 1){
          rank
          title
        }
      }
      images
    }
  }
}
"""
