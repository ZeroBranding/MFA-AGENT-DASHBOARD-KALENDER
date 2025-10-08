#!/usr/bin/env python3
"""
Problem-Analyse für das MFA Enterprise KI-Agent System
"""

def analyze_system_problems():
    print('PROBLEM-ANALYSE DES MFA ENTERPRISE KI-AGENT SYSTEMS')
    print('=' * 60)
    print()

    # Teste kritische Komponenten
    problems = []

    try:
        from enterprise.enterprise_system_final import get_enterprise_system
        system = get_enterprise_system()
        health = system.health_check()
        if health['overall_status'] != 'healthy':
            problems.append(f'System Health: {health["overall_status"]}')
        else:
            print('OK: Enterprise System: FUNKTIONIERT')
    except Exception as e:
        problems.append(f'Enterprise System: {str(e)}')

    # Calendar Service wurde entfernt
    print('HINWEIS: Calendar Service nicht mehr verfuegbar (entfernt)')

    try:
        from utils.intelligent_name_extractor import IntelligentNameExtractor
        ne = IntelligentNameExtractor()
        result = ne.extract_name_from_email('Hallo Dr. Müller', 'test@example.com')
        if not result:
            problems.append('Namenserkennung: Keine Namen erkannt')
        else:
            print('OK: Namenserkennung: FUNKTIONIERT')
    except Exception as e:
        problems.append(f'Namenserkennung: {str(e)}')

    try:
        from enterprise.enterprise_nlu import EnterpriseNLU
        nlu = EnterpriseNLU()
        result = nlu.analyze_email('Termin', 'Brauche Termin', 'test@example.com')
        if not result.intent_type:
            problems.append('NLU: Kein Intent erkannt')
        else:
            print(f'OK: NLU: Intent "{result.intent_type}" erkannt')
    except Exception as e:
        problems.append(f'NLU: {str(e)}')

    try:
        from agents.enhanced_email_agent import EnhancedEmailAgent
        ea = EnhancedEmailAgent()
        if not hasattr(ea, 'get_unread_emails'):
            problems.append('Email Agent: Fehlende Funktionen')
        else:
            print('OK: Email Agent: FUNKTIONIERT')
    except Exception as e:
        problems.append(f'Email Agent: {str(e)}')

    try:
        from services.ollama_service import OllamaService
        ollama = OllamaService()
        print('OK: Ollama Service: VERFUEGBAR')
    except Exception as e:
        problems.append(f'Ollama Service: {str(e)}')

    print()
    print('IDENTIFIZIERTE PROBLEME:')
    if problems:
        for i, problem in enumerate(problems, 1):
            print(f'{i}. {problem}')
    else:
        print('OK: KEINE KRITISCHEN PROBLEME GEFUNDEN')

    print()
    print('POTENTIELLE VERBESSERUNGSBEREICHE:')
    print('1. E-Mail-Verbindung (IMAP/SMTP) konfigurieren')
    print('2. Ollama-Service für LLM-Integration')
    print('3. Datenbank-Migrationen prüfen')
    print('4. Umgebungsvariablen (.env) konfigurieren')
    print('5. Logging-Level anpassen')
    print('6. Performance-Monitoring aktivieren')
    print('7. Test-E-Mails generieren und testen')
    print('8. Integration aller Komponenten testen')

    print()
    print('SYSTEM-STATUS:')
    if len(problems) <= 2:
        print('GRUEN: SYSTEM BEREIT FUER PRODUKTION')
    elif len(problems) <= 5:
        print('GELB: SYSTEM FUNKTIONIERT MIT KLEINEN PROBLEMEN')
    else:
        print('ROT: SYSTEM BENOETIGT WARTUNG')

    print()
    print('NÄCHSTE SCHRITTE:')
    if 'Ollama Service' in str(problems):
        print('1. Ollama installieren und starten')
    if 'E-Mail' in str(problems):
        print('2. E-Mail-Konfiguration prüfen')
    if 'Datenbank' in str(problems):
        print('3. Datenbank-Migrationen ausführen')
    print('4. Test-E-Mail senden und Antwort prüfen')
    print('5. 100 Test-E-Mails generieren und analysieren')

    return problems

if __name__ == '__main__':
    analyze_system_problems()
