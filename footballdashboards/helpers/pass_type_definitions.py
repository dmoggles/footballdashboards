import abc
import pandas as pd


class PassTypeDefinition(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def label(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def mask(cls, data: pd.DataFrame):
        pass

    @classmethod
    @abc.abstractmethod
    def _line_kwargs(cls):
        pass

    @classmethod
    def get_line_kwargs(cls):
        kwargs = cls._line_kwargs()
        if "linewidth" not in kwargs:
            kwargs["linewidth"] = 3
        if "comet" not in kwargs:
            kwargs["comet"] = True
        if "capstyle" not in kwargs:
            kwargs["capstyle"] = "round"
        if "transparent" not in kwargs:
            kwargs["transparent"] = True
        return kwargs


class RegularPassComplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "completed passes"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 1) & (data["passtypes"] == 0)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#e6b0aa", "zorder": 5}


class RegularPassIncomplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "incomplete passes"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 0) & (data["passtypes"] == 0)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#943126", "zorder": 6}


class ProgressivePassComplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "completed progressive passes"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 1) & (data["passtypes"] == 2)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#aed6f1", "zorder": 5}


class ProgressivePassIncomplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "incomplete progressive passes"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 0) & (data["passtypes"] == 2)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#2874a6", "zorder": 6}


class CutbacksComplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "completed cutbacks"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 1) & (data["passtypes"] % 2 == 1)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#58d68d", "zorder": 5}


class CutbacksIncomplete(PassTypeDefinition):
    @classmethod
    def label(cls):
        return "incomplete cutbacks"

    @classmethod
    def mask(cls, data: pd.DataFrame):
        return (data["outcomeType"] == 0) & (data["passtypes"] % 2 == 1)

    @classmethod
    def _line_kwargs(cls):
        return {"color": "#1d8348", "zorder": 6}
