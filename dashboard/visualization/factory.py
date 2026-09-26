"""ChartSpec에 맞는 Builder를 반환하는 팩토리."""
from __future__ import annotations

from dashboard.config.theme import ThemeConfig
from dashboard.models.dataset import Dataset
from dashboard.visualization.builders import (
    BarChartBuilder,
    ChartBuilder,
    ChartSpec,
    PieChartBuilder,
    TableBuilder,
)


class ChartFactory:
    _registry: dict[str, type[ChartBuilder]] = {
        "bar": BarChartBuilder,
        "pie": PieChartBuilder,
        "table": TableBuilder,
    }

    def __init__(self, theme: ThemeConfig) -> None:
        self.theme = theme

    @classmethod
    def register(cls, chart_type: str, builder_cls: type[ChartBuilder]) -> None:
        """새 차트 타입을 등록한다 (확장 지점).

        입력: chart_type — ChartSpec.chart_type에 쓰일 새 식별자(예: "radar").
              builder_cls — ChartBuilder를 상속한 새 빌더 클래스 (인스턴스 아님).
        동작: cls._registry에 {chart_type: builder_cls}를 추가한다.
        반환: 없음. 이후 create(ChartSpec(chart_type))으로 이 빌더를 바로 쓸 수 있다.
        """
        cls._registry[chart_type] = builder_cls

    def create(self, spec: ChartSpec) -> ChartBuilder:
        """차트 타입에 해당하는 Builder 인스턴스를 반환한다.

        입력: spec — spec.chart_type("bar"/"line"/... 중 하나)만 우선 참조한다.
        동작: self._registry에서 spec.chart_type에 맞는 클래스를 찾아
              self.theme을 주입해 인스턴스화한다.
        반환: 해당 차트 타입의 ChartBuilder 인스턴스. 등록되지 않은
              chart_type이면 KeyError (또는 ChartRenderError로 감싸는 것을 권장).
        """
        builder_cls = self._registry[spec.chart_type]
        return builder_cls(self.theme)

    def available_types(self) -> list[str]:
        """지원 차트 타입 목록.

        입력: 없음.
        동작: self._registry에 등록된 키들을 나열한다.
        반환: 등록된 chart_type 문자열 리스트 (예: ["bar", "line", ...]).
        """
        return list(self._registry)

    def recommend(self, dataset: Dataset) -> list[ChartSpec]:
        """데이터 스키마 기반 차트 자동 추천 (미구현).

        입력: dataset — schema(각 컬럼의 role: "measure"/"dimension"/"time")를
              담고 있는 Dataset.
        동작(완성판 기준): schema를 훑어 "time + measure가 있으면 line",
              "dimension + measure면 bar", "measure가 2개 이상이면 scatter"
              같은 규칙으로 어울리는 조합을 골라 ChartSpec을 만든다.
        반환: 추천 ChartSpec 리스트 (우선순위 순). 지금은 항상 빈 리스트.
        """
        return []
