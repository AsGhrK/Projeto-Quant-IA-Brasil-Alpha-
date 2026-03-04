def recommend_strategy(score, perfil):
    
    if perfil == "conservador":
        if score >= 70:
            return "ETF + Renda Fixa 50/50"
        elif score >= 50:
            return "70% Renda Fixa + 30% ETF"
        else:
            return "Renda Fixa predominante"

    elif perfil == "moderado":
        if score >= 70:
            return "60% Ações / 40% Renda Fixa"
        elif score >= 50:
            return "50% Ações / 50% Renda Fixa"
        else:
            return "30% Ações / 70% Renda Fixa"

    elif perfil == "agressivo":
        if score >= 70:
            return "80% Ações / 20% Caixa"
        elif score >= 50:
            return "60% Ações"
        else:
            return "40% Ações + Hedge"

    else:
        return "Perfil inválido"