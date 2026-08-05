import asyncio
from app.models.resume import ResumeProfile, WorkExperience, Education
from app.storage.resume_repository import ResumeRepository

def build_profiles() -> list[ResumeProfile]:
    # Profile 1: Back-End / Java Software Engineer
    profile_swe = ResumeProfile(
        profile_id="software_engineer_java",
        target_role_category="Back-End Software Engineering (Java / Spring)",
        full_name="Software Engineering Candidate",
        email="candidate@example.com",
        phone=None,
        linkedin_url="https://github.com/Dmuniiz",
        summary=(
            "Estudante de Engenharia de Software com foco em desenvolvimento back-end Java e ecossistema Spring. "
            "Experiência na construção de APIs REST seguras e escaláveis utilizando Spring Boot, Spring Security, JPA/Hibernate "
            "e PostgreSQL, aplicando boas práticas de arquitetura (SOLID, Design Patterns, testes automatizados). "
            "Possui forte capacidade analítica oriunda de suporte de alta complexidade em incidentes críticos."
        ),
        core_skills=[
            "Java", "Spring Boot", "Spring MVC", "Spring Data JPA", "Spring Security",
            "APIs REST", "JWT", "OAuth2", "PostgreSQL", "SQL", "Flyway", "Docker",
            "Docker Compose", "JUnit", "Mockito", "SOLID", "Design Patterns", "Git/GitHub", "Linux", "AWS"
        ],
        experiences=[
            WorkExperience(
                company="Concentrix",
                role_title="Support Advisor – L4",
                dates="12/2024 – Present",
                location="São Paulo, Brasil",
                highlights=[
                    "Garantia de 3 promoções em 18 meses até a posição máxima L4.",
                    "Ponto focal definitivo de escalonamento (L4), diagnosticando e resolvendo problemas complexos em sistemas operacionais e aplicações.",
                    "Análise de Causa Raiz (RCA) e implementação de soluções de contorno para redução do MTTR.",
                    "Mentoria técnica para analistas N1, N2 e N3 compartilhando metodologias de diagnóstico.",
                    "Comunicação cross-functional traduzindo problemas técnicos para times de engenharia e stakeholders."
                ]
            )
        ],
        education=[
            Education(
                institution="USJT",
                degree="Bacharelado em Engenharia de Software",
                field_of_study="Engenharia de Software",
                graduation_year="2027"
            ),
            Education(
                institution="ETEC Vila Formosa",
                degree="Técnico em Desenvolvimento de Sistemas",
                field_of_study="Desenvolvimento de Sistemas",
                graduation_year="2023"
            )
        ],
        certifications=["AWS Cloud Practitioner (Em andamento)", "ITIL 4 Foundation (Planejado)"]
    )

    # Profile 2: Support Engineering / Ops & Automation
    profile_ops = ResumeProfile(
        profile_id="support_ops_engineer",
        target_role_category="L4 Support Engineering / Operations & Automation",
        full_name="Support & Ops Engineering Candidate",
        email="candidate@example.com",
        phone=None,
        linkedin_url=None,
        summary=(
            "Profissional de Suporte de TI / Ops L4 com experiência em troubleshooting avançado, gestão de incidentes críticos "
            "e análise de causa raiz (RCA). Atua como camada final de escalonamento para incidentes complexos. "
            "Possui forte conhecimento em automação de processos e AI Workflows com n8n e Python, scripts para análise de logs, "
            "sistemas operacionais (macOS, Windows, Linux, iOS), redes e suporte a aplicações."
        ),
        core_skills=[
            "Troubleshooting Avançado (L1-L4)", "Análise de Causa Raiz (RCA)", "Gestão de Incidentes (ITIL)",
            "SLAs & MTTR Reduction", "Automação com n8n", "Python", "Shell Script / Bash",
            "Coleta e Análise de Logs", "LLMs & OpenAI APIs", "macOS", "iOS", "Windows", "Linux",
            "Redes (DNS, HTTP, TCP/IP, VPN)", "AWS (Fundamentos)", "Docker", "Git/GitHub"
        ],
        experiences=[
            WorkExperience(
                company="Concentrix",
                role_title="Support Advisor Level 4",
                dates="Dez/2024 – Present",
                location="São Paulo, Brasil",
                highlights=[
                    "Camada final de escalonamento técnico para incidentes avançados em macOS, Windows e iOS.",
                    "Execução de Análise de Causa Raiz (RCA) para falhas em software, SO e fluxos operacionais.",
                    "Análise automatizada de logs utilizando scripts para identificação de falhas sistêmicas.",
                    "Aderência rigorosa a SLAs operacionais e mentoria técnica para redução do MTTR.",
                    "Tradução de incidentes técnicos complexos para times de engenharia de produto."
                ]
            )
        ],
        education=[
            Education(
                institution="USJT",
                degree="Bacharelado em Engenharia de Software",
                field_of_study="Engenharia de Software",
                graduation_year="2027"
            ),
            Education(
                institution="ETEC Vila Formosa",
                degree="Técnico em Desenvolvimento de Sistemas",
                field_of_study="Desenvolvimento de Sistemas",
                graduation_year="2023"
            )
        ],
        certifications=["AWS Cloud Practitioner (Em andamento)"]
    )

    return [profile_swe, profile_ops]

def main():
    repo = ResumeRepository(data_dir="data")
    profiles = build_profiles()
    
    for p in profiles:
        repo.register_profile(p)
        repo.save_to_disk(p.profile_id)
        print(f"Successfully registered and saved: {p.profile_id}")

if __name__ == "__main__":
    main()