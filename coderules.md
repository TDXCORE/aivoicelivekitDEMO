A continuación tienes un manual técnico en Markdown con las reglas, estándares y mejores prácticas que todo equipo de desarrollo debe seguir. Cada punto está diseñado para ser implementable como checklist de revisión continua.

Resumen rápido
Diseño limpio y extensible (SOLID, ISO 25010).

Control de versiones disciplinado (TB-Dev + SemVer).

Seguridad “shift-left” (OWASP SCP + SDL).

Calidad garantizada (Pirámide de pruebas + CI/CD).

Infraestructura versionada (IaC con Terraform).

Fiabilidad medible (SLI/SLO/SLA estilo SRE).

1. Diseño y Código
text
Copiar
Editar
✓ Aplicar SOLID en todas las clases y módulos
✓ Nombres claros, pronunciables y sin “magia”
✓ Revisar mantenibilidad, seguridad y performance contra ISO 25010
SOLID: SRP, OCP, LSP, ISP, DIP para un código extensible y testable. 
digitalocean.com

Clean Code Naming: nombres descriptivos, constantes en lugar de números mágicos, evitar prefijos tipo húngaro. 
medium.com

Calidad ISO 25010: medir mantenibilidad, fiabilidad, usabilidad y seguridad de forma explícita en Definition of Done. 
iso25000.com

2. Control de Versiones
text
Copiar
Editar
✓ Trunk-Based Development
✓ Commits semánticos
✓ Pull Request obligatorio
TB-Dev: commits pequeños hacia la rama principal con feature flags para desplegar varias veces al día. 
atlassian.com

Semantic Versioning: MAJOR.MINOR.PATCH-PRERELEASE+BUILD para todas las librerías y servicios. 
semver.org

3. Seguridad by Design
text
Copiar
Editar
✓ Checklist OWASP en cada PR
✓ Threat-modeling en fase de diseño
✓ Secrets en vault, MFA obligatorio
OWASP Secure Coding Checklist: validación de entradas, gestión de sesiones, control de acceso y cifrado por defecto. 
owasp.org

Microsoft SDL: actividades de requisitos → diseño → implementación → verificación → publicación con gates de seguridad. 
learn.microsoft.com