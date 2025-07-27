flowchart TD
  %% ========= CHAT MODAL =========
  A["Chat Modal\nopens"] --> B{Messages present?}
  B -- No --> ES["Empty-State\n(big suggestions list)"]
  ES -->|Tap Suggestion| SendMsg
  B -- Yes --> CV["Chat Conversation View"]
  CV -->|User taps Recipe Card| RD

  %% ========= PRE-CANNED QUESTIONS =========
  subgraph Suggestions
    direction TB
    S1["What can I make for dinner?"]
    S2["What can I make with only ingredients I have?"]
    S3["What’s good for breakfast?"]
    S4["Show me healthy recipes"]
    S5["Quick meals under 20 minutes"]
    S6["What should I cook tonight?"]
  end
  S1 --> ES
  S2 --> ES
  S3 --> ES
  S4 --> ES
  S5 --> ES
  S6 --> ES
  S1 --> QS["Inline quick suggestions"]
  S2 --> QS
  S3 --> QS
  S4 --> QS
  S5 --> QS
  S6 --> QS
  QS -->|Tap| SendMsg

  %% ========= CHAT API & DATA FLOW =========
  subgraph API["Chat Backend"]
    SendMsg["sendChatMessage() - POST /chat/message"]
    SendMsg -->|AI response including recipes| OnReply
  end
  OnReply --> CV

  %% ========= RECIPE DETAIL =========
  subgraph RDgrp["RecipeDetailCardV2 (RD)"]
    direction TB
    RD["Recipe Detail Screen"]
    RD --> Img["Hero image & metadata"]
    RD --> IngList["Ingredients list"]
    RD --> Steps["Cooking steps"]
    RD --> BottomBtns["Bottom action bar"]
    BottomBtns --> CookBtn["Cook Now"]
    BottomBtns --> QuickBtn["Quick Complete"]
    BottomBtns --> Bookmark["Bookmark ♡"]
    BottomBtns --> Rating["Thumbs Up / Down"]
  end

  %% ========= ACTION FLOWS =========
  %% Cook Now flow
  CookBtn -->|router push to cooking mode| CM["Cooking-Mode Screen"]
  CM --> FinishBtn["Finish Cooking"]
  FinishBtn -->|handle finish cooking - POST /api/v1/recipe-consumption/complete| CMDone["Show rating modal"]

  %% Quick Complete flow
  QuickBtn --> QCModal["QuickCompleteModal"]
  QCModal -->|Confirm| QuickAPI["POST /api/v1/recipe-consumption/quick-complete"]
  QuickAPI --> QCResult["Success toast ➜ navigate back"]

  %% Bookmark toggle
  Bookmark -->|Save| SaveAPI["(PATCH /recipes/save)"]
  Bookmark -->|Un-save| UnsaveAPI["(DELETE /recipes/save)"]

  %% Rating
  Rating -->|Open modal and POST /recipes/rate| RateAPI["(POST /recipes/rate)"]
