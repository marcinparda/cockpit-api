"""
Seed script for populating the Redis store with base CV data.

Usage:
    docker compose -f docker-compose.dev.yml run --rm cockpit_api python scripts/seed_redis_store.py

    Or with a custom Redis URL:
    REDIS_STORE_URL=redis://localhost:6379 python scripts/seed_redis_store.py
"""
import asyncio
import json
from datetime import datetime, timezone
from os import getenv

import redis.asyncio as redis

REDIS_URL = getenv("REDIS_STORE_URL", "redis://cockpit_redis:6379")

NOW = datetime.now(timezone.utc).isoformat()


def envelope(key: str, type_: str, tags: list[str], data: object) -> dict:
    return {
        "meta": {
            "key": key,
            "type": type_,
            "version": 1,
            "created_at": NOW,
            "updated_at": NOW,
            "tags": tags,
        },
        "data": data,
    }


CV_DATA: list[tuple[str, dict]] = [
    (
        "base:cv:header",
        envelope(
            key="base:cv:header",
            type_="cv_section",
            tags=["cv", "header"],
            data={
                "name": "MARCIN PARDA",
                "title": "Senior Frontend Developer with Python",
                "phone": "+48 576 259 548",
                "email": "marcin98parda@gmail.com",
                "linkedin": {
                    "url": "www.linkedin.com/in/marcinparda/",
                    "text": "linkedin.com/in/marcinparda",
                },
                "location": "Warsaw, Poland",
            },
        ),
    ),
    (
        "base:cv:summary",
        envelope(
            key="base:cv:summary",
            type_="cv_section",
            tags=["cv", "summary"],
            data=[
                "Specialist with 5.5 years of experience, including over 2 years as a senior developer. "
                "Acting as a code mentor and technical recruiter. Regular speaker inside organization and "
                "seasoned speaker at external IT meetings and blogger. Active participant in events such as "
                "Advent of Code and hackathons. More about me: https://www.parda.me/work",
            ],
        ),
    ),
    (
        "base:cv:skills",
        envelope(
            key="base:cv:skills",
            type_="cv_section",
            tags=["cv", "skills"],
            data=[
                {"name": "React", "years": 5, "description": "Primary frontend framework used across all professional projects."},
                {"name": "TypeScript", "years": 5, "description": "Default language for all frontend development."},
                {"name": "Node.js", "years": 4, "description": "Backend runtime for JS-based services and tooling."},
                {"name": "Nx", "years": 3, "description": "Monorepo tooling; led migration from microfrontend to Nx monorepo."},
                {"name": "AI agents / MCP", "years": 1, "description": "Building and integrating AI agents and MCP servers."},
                {"name": "Vitest / Cypress / Jest", "years": 4, "description": "Testing across unit, integration, and e2e layers."},
                {"name": "Next.js", "years": 2, "description": "Used for SSR and static site generation projects."},
                {"name": "Vue / Astro / Angular", "years": 3, "description": "Secondary frameworks used in various client projects."},
                {"name": "FastAPI", "years": 3, "description": "Primary Python framework for backend API development."},
                {"name": "Python", "years": 3, "description": "Used for backend services, AI tooling, and scripting."},
                {"name": "Postgres", "years": 3, "description": "Primary relational database."},
                {"name": "Redis", "years": 1, "description": "Used for caching, session storage, and personal data store."},
                {"name": "Docker", "years": 3, "description": "All projects containerized; deployed on Raspberry Pi via Docker."},
                {"name": "SQLAlchemy", "years": 3, "description": "ORM for async database operations in FastAPI projects."},
                {"name": "express.js", "years": 2, "description": "Node.js web framework for lightweight backend services."},
                {"name": "English B2", "years": 0, "description": "Professional working proficiency."},
                {"name": "Polish Native", "years": 0, "description": "Native language."},
            ],
        ),
    ),
    (
        "base:cv:achievements",
        envelope(
            key="base:cv:achievements",
            type_="cv_section",
            tags=["cv", "achievements"],
            data=[
                {
                    "title": "Helped excels carrier of my mentees and mine",
                    "description": "I mentored several colleagues who consistently excelled and received promotions. My own achievements led to a rapid promotion from 'early senior' to a higher position within a year.",
                },
                {
                    "title": "Delivering with cut budget",
                    "description": "As sole developer, I reduced development time from six to four months. We delivered a minimalistic product, and the client returned with more budget for further work.",
                },
                {
                    "title": "Awarded 'SPOT award' & 'Consulting People Champion' bonus",
                    "description": "I led a side project automating CV updates, saving 0.5 hours monthly for each of over 100 employees which resulted in receiving the 'SPOT award'. Also I was awarded 'Consulting People Champion' award for my dedication to mentoring and supporting colleagues.",
                },
                {
                    "title": "Increased employment",
                    "description": "Successfully expanded my company's team presence at the client's site by delivering the project from initial client workshops through to a functional Minimum Viable Product (MVP), which led to the client hiring additional personnel from my company.",
                },
            ],
        ),
    ),
    (
        "base:cv:experience",
        envelope(
            key="base:cv:experience",
            type_="cv_section",
            tags=["cv", "experience"],
            data=[
                {
                    "title": "Senior Frontend Developer + Backend (Python)",
                    "company": "Agro (Second Job)",
                    "date": "09/2025 - Present",
                    "location": "Remote",
                    "description": [
                        "Developed a full-stack agriculture management application with Django REST Framework and React TypeScript.",
                        "Implemented Progressive Web App (PWA) with offline mode support, enabling field work without internet connectivity.",
                        "Integrated Leaflet maps with offline tile caching for geospatial field management and visualization.",
                        "Worked with Django and PostGIS for backend GIS functionality, handling spatial data and queries.",
                        "Made key architecture and technical decisions collaboratively with programming team members.",
                        "Built map-based features for field management, trip tracking, sampling grids, and lab examination visualization.",
                        "Worked with AI tools and workflows to speed up development and prototyping.",
                        "Refactor app from monolith to modular monolith architecture to improve maintainability and scalability.",
                    ],
                },
                {
                    "title": "Senior Developer",
                    "company": "EY GDS (BIG4)",
                    "date": "11/2023 - Present",
                    "location": "Warsaw, Poland",
                    "description": [
                        "Successfully led a team developing internal applications; handled requirements gathering with managers, authored user stories, assigned tasks, set priorities for architecture and complex feature development, and facilitated a smooth project handover to management.",
                        "Spearheaded the migration from a broken microfrontend solution to a monorepo architecture for five projects, enabling easier code sharing, simplifying new project creation, and reducing deployment times from ~40min to ~10min.",
                        "Worked with a system that handles changes in real time communication with backend via SignalR, ensuring seamless data updates and user interactions.",
                        "Orchestrated migration initiatives from legacy frameworks and infrastructure. Delivered React upgrade and a full UI overhaul across all pages, both delivered on schedule and resulting in zero major bugs or design inconsistencies.",
                        "Created and maintained a detailed frontend developer competence matrix, accelerating the on-boarding and learning skills assessment for employees using a technical problem-solving skills.",
                        "Coordinated knowledge-sharing meetings within the frontend & design department, fostering learning and best practices across teams by participating in industry events and community.",
                        "Contributed to multiple proof-of-concept projects, including an AI RAG-based chatbot (web components + Flask) designed for easy integration into other solutions.",
                        "Built and maintained design component libraries using Storybook for two key projects, improving UI consistency, docs and reusability.",
                        "Resolved a persistent login issue by forking and updating the MSAL library, ensuring stable authentication for end users.",
                        "Gained valuable insights and work-ethics lessons about documentation, testing, code reviews, and sprint refinement through close collaboration with an experienced tech lead, leading to more accurate task estimation and flawless sprint goal delivery.",
                    ],
                },
                {
                    "title": "Javascript Developer",
                    "company": "STX Next (continuation of work at Ermlab Software)",
                    "details": "AI Python software house",
                    "date": "04/2022 - 11/2023",
                    "location": "Olsztyn, Poland",
                    "description": [
                        "Speeded up internal screens of internal applications from ~5s to less than 0.5s via refactor.",
                        "Planned frontend architecture multiple times, selecting appropriate tools and libraries for new projects.",
                        "Learned a Python extension development and created a MVP of an extension project before estimated time.",
                        "Developed a mobile application for vets and patients.",
                        "Implemented integration systems.",
                        "Provided assistance and guidance to other Team members.",
                        "Participated in additional activities such as AI hackathons (manage to won!), Tech Talks, and Meetups.",
                    ],
                },
                {
                    "title": "Frontend Developer",
                    "company": "Ermlab Software",
                    "details": "AI Python software house",
                    "date": "07/2020 - 03/2022",
                    "location": "Olsztyn, Poland",
                    "description": [
                        "Worked on developing and maintaining frontend projects in React and Angular technologies.",
                        "Created complex multistep forms, web applications with facebook auth.",
                        "Created data visualization for AI scientific research.",
                        "Co-created Google Chrome extension.",
                        "Technically supervising learning meetings and leading several of them.",
                    ],
                },
            ],
        ),
    ),
    (
        "base:cv:education",
        envelope(
            key="base:cv:education",
            type_="cv_section",
            tags=["cv", "education"],
            data=[
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "university": "University of Warmia and Mazury in Olsztyn",
                    "years": "2017 - 2021",
                },
            ],
        ),
    ),
    (
        "base:cv:projects",
        envelope(
            key="base:cv:projects",
            type_="cv_section",
            tags=["cv", "projects"],
            data=[
                {
                    "name": "Blog",
                    "liveUrl": "https://www.parda.me/blog",
                    "code": "https://github.com/marcinparda/parda.me",
                    "date": "03/2023 - Present",
                    "description": [
                        "Technical blog where I write about web development topics.",
                        "Primarily cover front-end development, but I also cover topics related to working as a developer.",
                        "Trying to keep them short but understandable, using real-life scenarios for better understanding.",
                        "Trying to write posts monthly.",
                    ],
                },
                {
                    "name": "Cockpit",
                    "liveUrl": "https://www.cockpit.parda.me",
                    "code": "https://github.com/marcinparda/cockpit-api & https://github.com/marcinparda/cockpit-app",
                    "date": "03/2023 - Present",
                    "description": [
                        "Cockpit project consists of several apps that help boost my productivity and overall quality of life, such as managing my budget and assisting with newsletters.",
                        "FastAPI backend for frontend applications. Using Postgres, SQLAlchemy, Pydantic.",
                        "NX monorepo for my frontend applications. Using React, Angular, Vue, OpenAPI types generation, tailwindcss, vitest.",
                        "Docker & Raspberry Pi Deployment",
                    ],
                },
            ],
        ),
    ),
    (
        "base:cv:courses",
        envelope(
            key="base:cv:courses",
            type_="cv_section",
            tags=["cv", "courses"],
            data=[
                "Microsoft Certified: Azure AI Fundamentals",
                "Microsoft Certified: Azure Fundamentals",
                "AI Devs 2 & 3 - AI integration and building agents",
                "Architecture on Frontend (Architektura na Froncie)",
                "FastAPI masterclass from scratch",
                "Modern Frontend - Next.js, React, GraphQL and Typescript",
            ],
        ),
    ),
]


async def seed() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    try:
        await client.ping()
        print(f"Connected to Redis at {REDIS_URL}")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return

    seeded = 0
    skipped = 0

    for redis_key, data in CV_DATA:
        existing = await client.json().get(redis_key, "$")
        if existing:
            print(f"  SKIP  {redis_key} (already exists)")
            skipped += 1
            continue

        await client.json().set(redis_key, "$", data)
        print(f"  SET   {redis_key}")
        seeded += 1

    await client.aclose()
    print(f"\nDone. Seeded: {seeded}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
