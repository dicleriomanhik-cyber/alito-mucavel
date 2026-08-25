"""
Script de seed — insere os pacotes iniciais na base de dados.

Corre-se UMA VEZ (localmente, apontando ao DATABASE_URL real do Render/Supabase/
Neon) para povoar a tabela de pacotes. Depois disso, todas as alterações
(preços, descrições, ativar/desativar, criar novos) fazem-se pelo painel
admin — este script não precisa de ser corrido de novo.

Uso:
    cd backend
    source venv/bin/activate
    python -m scripts.seed_packages

Os preços marcados como "PLACEHOLDER" são valores de exemplo — o Alito deve
corrigi-los no painel admin (secção "Pacotes e preços") antes de publicar.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.models import Package

PACKAGES: list[dict] = [
    # ---------------- CASAMENTO (dois pacotes) ----------------
    {
        "name": 'Pacote Diamante — "O Produtor do Amor + Guardião da Tradição"',
        "event_type": "Casamento",
        "description": (
            "Para quem quer viver o dia como um Rei e uma Rainha, sem "
            "preocupações, e honrar a cultura que nos une. Vou além da "
            "campainha do salão: acompanho o casal desde os momentos tensos "
            "da Conservatória até à tradicional cerimónia do Xiguiane na "
            "casa dos sogros. Os convidados não são plateia — são atores "
            "principais de um espetáculo inesquecível."
        ),
        "base_price": 85000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Acompanhamento na Conservatória: chego antes de todos para organizar as testemunhas e acalmar os nervos, e comando a saída dos noivos com chuva de pétalas sincronizada",
            '"Tribunal do Amor": leitura dramatizada de mensagens emocionantes dos pais e amigos, desafiando os noivos a adivinharem quem escreveu cada uma',
            'Chamamento oficial dos presentes ("Desfile da Machamba"): desfile organizado por núcleos familiares, com narração personalizada para cada grupo',
            'Jogo de afinidade "Boca a Boca": noivos de costas um para o outro, com perguntas picantes e divertidas sobre o relacionamento',
            "Passarela Diamante: eleição dos 5 convidados mais elegantes, com desfile ao som de Kizomba e brinde para o vencedor",
            'Bónus "Livro dos Sonhos": leitura das mensagens mais tocantes escritas por crianças e avós no Livro de Ouro',
            "Condução completa do Xiguiane na casa dos sogros: coordenação da chegada da família da noiva, cânticos, danças tradicionais, entrega dos simbólicos, e falas em Changana/Português com respeito e emoção",
            "Duração: jornada completa (Conservatória + Salão + Xiguiane), até ao último 'parabéns' na casa nova",
        ],
        "is_active": True,
    },
    {
        "name": 'Pacote Ouro — "O Controlo do Salão"',
        "event_type": "Casamento",
        "description": (
            "Para quem quer o essencial, mas com classe e pontualidade. "
            "Ideal para o casal que já tem tudo planeado, mas precisa de "
            "uma voz de comando firme, divertida e profissional para o "
            "cronograma não descarrilar. Foco total dentro das quatro "
            "paredes do salão."
        ),
        "base_price": 45000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Receção de gala: entrada triunfal dos noivos com a música escolhida a dedo",
            "Mestre das palavras: condução dos discursos dos padrinhos e pais, com tempo controlado com educação",
            "Ritual do bolo: comando do momento do corte, brinde e pose para as fotografias oficiais",
            "Abertura da pista: arranque da festa com Semba e Marrabenta para ninguém ficar sentado",
            "Duração: atuação exclusiva no salão (até 7 horas de evento)",
        ],
        "is_active": True,
    },
    # ---------------- OUTROS EVENTOS (um pacote cada) ----------------
    {
        "name": "Pacote Corporativo — Presença e Profissionalismo",
        "event_type": "Corporativo",
        "description": (
            "Para conferências, lançamentos de produto e galas empresariais "
            "que precisam de uma condução segura do programa, sem perder o "
            "carisma que mantém a audiência atenta."
        ),
        "base_price": 35000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Receção institucional dos convidados e apresentação da agenda",
            "Condução do programa e apresentação dos oradores/painéis",
            "Gestão de tempo dos discursos e sessões de perguntas e respostas",
            "Dinâmica de networking ou quebra-gelo nos intervalos",
            "Encerramento com síntese do evento e agradecimentos oficiais",
            "Duração: até 6 horas de evento",
        ],
        "is_active": True,
    },
    {
        "name": "Pacote Toga de Ouro — A Consagração do Esforço",
        "event_type": "Graduação",
        "description": (
            "Para celebrar o percurso académico com a solenidade que "
            "merece, entre a entrega de diplomas e a festa em família."
        ),
        "base_price": 20000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Chamada individual dos formandos ao palco, com narração do seu percurso",
            "Condução da entrega de canudos/diplomas e fotografias oficiais",
            "Homenagem aos pais e professores, com espaço para palavras dos formandos",
            "Momento de brinde e corte do bolo de finalistas",
            "Abertura da pista de dança ao gosto da turma",
            "Duração: até 5 horas de evento",
        ],
        "is_active": True,
    },
    {
        "name": "Pacote Aniversário — A Sua História em Festa",
        "event_type": "Aniversário",
        "description": (
            "De festas íntimas em família a grandes celebrações, conduzo o "
            "programa com alegria, ritmo e boa disposição para todas as idades."
        ),
        "base_price": 15000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Animação e condução de jogos/brincadeiras conforme a idade do aniversariante",
            "Momento especial dos parabéns, com música e velas",
            "Dinâmicas de interação com os convidados (jogos, brindes)",
            "Condução do corte do bolo e fotografias",
            "Abertura da pista de dança",
            "Duração: até 4 horas de evento",
        ],
        "is_active": True,
    },
    {
        "name": "Pacote Xitique — Tradição e Confiança",
        "event_type": "Xitique",
        "description": (
            "Para celebrar o encontro do grupo de xitique com boa energia, "
            "transparência no momento de entrega dos valores e muita "
            "animação entre as participantes."
        ),
        "base_price": 8000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Condução do momento oficial de entrega/sorteio dos valores, com transparência e alegria",
            "Dinâmicas de interação e convívio entre as participantes",
            "Momento de agradecimento e reconhecimento às organizadoras",
            "Animação musical ao longo do encontro",
            "Duração: até 3 horas de evento",
        ],
        "is_active": True,
    },
    {
        "name": "Pacote Personalizado",
        "event_type": "Outro",
        "description": (
            "Todo evento é único — se o seu não se encaixa nas categorias "
            "acima, monto um programa à medida das suas necessidades, "
            "mantendo o mesmo profissionalismo e energia."
        ),
        "base_price": 20000,  # PLACEHOLDER — ajustar no admin
        "features": [
            "Reunião prévia para entender o formato e objetivo do evento",
            "Programa e guião de condução personalizados",
            "Condução ao vivo com adaptação ao ritmo do público",
            "Duração: a combinar conforme o evento",
        ],
        "is_active": True,
    },
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        inserted, skipped = 0, 0
        for data in PACKAGES:
            existing = await session.execute(
                select(Package).where(
                    Package.name == data["name"], Package.event_type == data["event_type"]
                )
            )
            if existing.scalar_one_or_none() is not None:
                print(f"[=] Já existe, a ignorar: {data['name']}")
                skipped += 1
                continue

            session.add(Package(**data))
            print(f"[+] Inserido: {data['name']} ({data['event_type']}) — {data['base_price']} MT (placeholder)")
            inserted += 1

        await session.commit()
        print(f"\nConcluído: {inserted} inseridos, {skipped} já existiam.")
        print("Lembrete: os preços são PLACEHOLDERS — ajusta-os no painel admin antes de publicar.")


if __name__ == "__main__":
    asyncio.run(seed())
