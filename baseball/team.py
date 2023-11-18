from baseball.players.player import Player
from baseball.players.hitter import Hitter
from baseball.players.pitcher import Pitcher



class Team:
    def __init__(self, players: list[Player, name: str) -> None:
        self.__name: str = name
        self.__players: dict[str, Player] = {
            p.name: p for p in players,
        }

    
    @property
    def players(self) -> list[Player]:
        return self.__players

