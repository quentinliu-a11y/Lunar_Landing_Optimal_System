# NASA Space Apps Challenge 2026 — reference notes

Collected from spaceappschallenge.org on 14 Nov 2026 (Singapore time). Paraphrased notes, not the official wording; check the linked pages before relying on a rule.

## 1. Event basics

- Dates: 14–15 November 2026. Theme: "The Next Frontier".
- Project submission opens Sat 14 Nov 09:00 and closes **Sun 15 Nov 23:59**, in the time zone of the team's Local Event (Universal Event: local time of the Team Owner's place of residence). Anything saved or submitted after the deadline is not judged.
- Teams: 1–6 members for a Local Event, 2–6 for the Universal Event. Everyone must be registered for the same event (not waitlisted) and appear on the team's Members tab. One team per person, one challenge per team. No new members after submission closes.
- Teams are not supposed to start work on a challenge before the hackathon.
- Results: Global Nominees 3 Dec 2026, Global Finalists and Honorable Mentions 17 Dec 2026, Global Winners 26 Jan 2027.

## 2. Our challenge: Lunar Landing Site Navigator

URL: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/
Difficulty: Intermediate / Advanced. Subjects: Human Exploration, Moon, Software, Space Exploration.

### The task
Build an intuitive tool or app that lets mission planners, educators and the public compare lunar landing sites and dates quickly, by showing where the Sun and Earth sit relative to the local horizon. Two things are assessed from that: power generation potential (Sun) and direct-to-Earth communication windows (Earth).

### Background in short
- CLPS and other lunar missions pick a site and date that satisfy both science and engineering teams.
- Sun position sets solar-array power and thermal conditions; Earth position sets whether direct communication works without a relay satellite.
- The south pole is the hard case: water ice makes it attractive, but illumination and Earth visibility vary strongly with lunar day and season, and a small change in place or date changes the result a lot.
- Schedules slip, so planners must re-evaluate nearby sites or new dates fast.
- Existing tools (Quickmap, Moon Trek, JPL Horizons) hold the data but are built for detailed analysis and are hard for non-specialists to use for quick scenario comparison. The gap is usability.

### Objectives (all optional, "may include")
1. Site selection and comparison: curated list of notable sites (Apollo, future CLPS targets, other commercial missions, other countries' landing sites) plus custom coordinates; side-by-side or sequential comparison.
2. Date and time flexibility: choose landing date/time, explore change across lunar days and seasons.
3. Sun and Earth position display relative to the horizon for a chosen site and date; time left until sunset or Earthset.
4. Power and communication metrics: solar elevation angle, sunlight duration, Earth visibility windows.
5. Several visualization styles: 2D maps, 3D surface, other creative forms.
6. Temporal dynamics: animations or timelines over one or several lunar days.
7. Usable by different skill levels: planners, educators, general public.

Format is open: web app, mobile app, interactive visualization, educational game, etc.

### Potential considerations (optional)
- Technical: ephemeris from JPL Horizons or pre-computed datasets; LOLA topography for realistic surface and horizon; no atmosphere, so no refraction and the horizon is set by local terrain and the lunar limb; show solar elevation angle prominently.
- User experience: fast scenario comparison; clear "time remaining before sunset/Earthset"; make lunar-versus-Earth differences visible; help users see why small changes have big effects.
- Data and accuracy: real topography; libration and lunar orbital variations; steep slopes and deep craters at the south pole that create extreme shadow.
- Engagement: support science/engineering coordination, quick response to schedule changes, and education.

### Official resources for this challenge
- Quickmap (ASU, LRO imagery and topography): https://quickmap.lroc.asu.edu/
- Moon Trek (NASA 3D lunar visualization, topography): https://trek.nasa.gov/moon/
- JPL Horizons System (ephemeris; Sun and Earth as seen from a point on the Moon): https://ssd.jpl.nasa.gov/horizons/
- CSA Moon Exploration portal (partner resource): https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/

LOLA is named in the challenge text as a topography source but is not linked on the Resources tab.

## 3. Judging

Each criterion is scored 1–5 at every judging level:

| Criterion | What judges look for |
|---|---|
| Impact | Size of the problem addressed and how many people it helps or inspires |
| Creativity | Novel concept or a meaningful improvement on existing ideas |
| Validity | Scientifically sound, technically feasible, complete, usable |
| Relevance | Directly answers the chosen challenge; NASA data is a core part, not decoration |
| Presentation | Clear, engaging story of challenge, solution and significance; based on demo plus full project |

The guide stresses giving Presentation as much attention as the other four.

Phases: Local/Universal judges pick Global Nominees → global judges pick Global Finalists and Honorable Mentions → an executive committee from NASA and partner agencies picks winners of ten Global Awards (Best Use of Science, Best Use of Data, Best Use of Technology, Galactic Impact, Best Mission Concept, Most Inspirational, Best Storytelling, Global Connection, Art & Technology, Local Impact).

### Eligibility for Global Judging
- Respond to one official challenge.
- Team membership rules in section 1 are met.
- All required fields on the Project page are complete.
- Demo provided: slide deck of **at most 7 slides** (title and intro included) or video of **at most 30 seconds**. Exceeding either limit makes the project ineligible.
- English on the project page and in all linked material. A demo video may be spoken in another language if it has English subtitles; slides must be in English.
- Both checkboxes ticked (terms and conditions; original work with all external resources listed in References, no unlicensed copyrighted material).
- Teams are reviewed under NASA's China funding restriction policy for prohibited bilateral activity with China or a Chinese-owned entity (including institutions incorporated under Chinese law, Hong Kong and Macau included). NASA decides eligibility at its own discretion, based on information the applicant provides. See the Terms and Conditions for how Chinese affiliation affects recognition as a Global Winner.
- To be eligible for a Global Award, the project must use at least one NASA data source or resource.

## 4. Project submission page

Access: profile icon → My Team → Project tab → Edit. Save often; use the edit Lock when editing; only the last saved submission is judged; the project can be edited and resubmitted until the deadline. Final step: tick both boxes and click "Submit for Judging".

Fields:
1. Project Name
2. High-Level Project Summary: what was built, how it addresses the challenge, why it matters
3. Link to Project Demo: 7 slides or 30-second video, hosted externally with a public link
4. Link to Final Project: public link (website, GitHub, Drive, YouTube, etc.)
5. Detailed Project Description: what it does, how it works, benefits, goals, tools and languages used
6. Use of Super Intelligence (SI): whether and how SI tools were used (not shown to judges)
7. NASA Data: specific NASA data and resources used
8. Space Agency Partner Data and Other References: every dataset, tool, code, text and image used

Files: images (JPG, PNG, GIF up to 10 MB) can be uploaded; videos and documents cannot and must be linked. Links must work without login, password or permission; test them in a private browser window. For a newly created website, a FortiGuard Web Filter Classification request is recommended (optional) so judges can open it.

### SI ("Super Intelligence", the site's term for AI) rules
- SI tools are allowed to speed up development and creativity; they should not be used to come up with the idea for solving the challenge.
- Usage must be described in the submission and marked in the project: SI-generated images and videos need a visible watermark; audio, code and data need an acknowledgement in descriptive text and metadata.
- Generated content may not use or modify NASA branding (logos, flags, mission identifiers).
- Judges can see the SI indicators in the project and weigh originality, intent and execution accordingly.

### Demo tips from the guide
- Suggested 30-second video outline: 0:00 team intro, 0:02 which challenge and why, 0:05 project title and tagline, 0:10 how it works with images or prototype and the NASA/partner data behind it, 0:20–0:30 future vision.
- Slides: readable template, few words, strong visuals; show an image of the project, the user experience, and how NASA and partner data make it possible; include team name, member names and the selected challenge.
- No images, video, audio or likeness of anyone under 18.

## 5. Source pages

- Challenges list: https://www.spaceappschallenge.org/2026/challenges/
- Challenge resources tab: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/?tab=resources
- Participant FAQs: https://www.spaceappschallenge.org/resources/participant-faqs/
- Judging & Awards Guide: https://www.spaceappschallenge.org/resources/judging-awards-guide/
- Project Submission Guide: https://www.spaceappschallenge.org/resources/project-submission-guide/
- Terms and legal: https://www.spaceappschallenge.org/legal/
- Space Apps Connect (forum): https://github.com/nasa/spaceapps
