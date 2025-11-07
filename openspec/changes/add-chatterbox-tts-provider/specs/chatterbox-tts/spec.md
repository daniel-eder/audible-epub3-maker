# Capability Spec: Chatterbox TTS Integration

## ADDED Requirements

### Requirement: Select Chatterbox TTS Engine
#### Scenario: CLI user picks chatterbox
Given the user runs the CLI with `--tts_engine chatterbox`
Then the system initializes the Chatterbox TTS provider
And uses configured environment variables for request parameters

#### Scenario: Default base URL applied
Given no `CHATTERBOX_TTS_URL` is set
Then the provider uses `http://localhost:4123`

### Requirement: Perform Text-to-Speech via HTTP
#### Scenario: Basic synthesis
Given chapter HTML with textual content
When the provider posts JSON `{input: <text>}` to `/v1/audio/speech`
Then it receives WAV bytes
And saves merged audio to the target file

#### Scenario: Apply optional parameters
Given environment variables `CHATTERBOX_EXAGGERATION`, `CHATTERBOX_CFG_WEIGHT`, `CHATTERBOX_TEMPERATURE`
When synthesis executes
Then these values are included in the JSON body if present

### Requirement: Heuristic Word Boundaries
#### Scenario: Generate pseudo boundaries
Given synthesized audio length L ms and N tokens
Then the provider computes boundaries with evenly partitioned ranges
And returns a non-empty list for downstream alignment

#### Scenario: Empty or single-token input
Given only one token
Then a single WordBoundary spans the entire audio duration

### Requirement: Error Handling
#### Scenario: HTTP failure
Given the API responds with non-200
Then raise an error containing status code and snippet of response text

#### Scenario: Zero-length audio
Given returned bytes produce an empty AudioSegment
Then raise TTSEmptyAudioError

### Requirement: Documentation & Compose Example
#### Scenario: README updated
Given a user searches README for "Chatterbox"
Then they find environment variables, usage example, and docker compose reference

#### Scenario: Docker compose example present
Given repository root
Then file `docker-compose.chatterbox.example.yml` exists with both services configured

## MODIFIED Requirements

### Requirement: TTS Engine Factory
#### Scenario: Factory supports chatterbox
Given call `create_tts_engine('chatterbox')`
Then returns an instance of ChatterboxTTS

## REMOVED Requirements
None.
