#!/bin/bash

# Detectar en qué rama estoy
current_branch=$(git branch --show-current)

# Función para chequear cambios pendientes
check_changes() {
  if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️ Tenés cambios sin commitear."
    read -p "¿Querés hacer git stash antes de cambiar de rama? (s/n): " answer
    if [[ "$answer" == "s" || "$answer" == "S" ]]; then
      git stash
      echo "✅ Cambios guardados en stash."
    else
      echo "⏩ No se guardaron los cambios."
    fi
  fi
}

# Lógica de alternancia
if [[ "$current_branch" == "main" ]]; then
  check_changes
  echo "🔄 Cambiando a migracion-postgres..."
  git checkout migracion-postgres
elif [[ "$current_branch" == "migracion-postgres" ]]; then
  check_changes
  echo "🔄 Cambiando a main..."
  git checkout main
else
  echo "⚠️ Estás en la rama '$current_branch', que no es ni 'main' ni 'migracion-postgres'."
  read -p "¿Querés cambiar a 'main'? (s/n): " go_main
  if [[ "$go_main" == "s" || "$go_main" == "S" ]]; then
    check_changes
    git checkout main
  fi
fi
