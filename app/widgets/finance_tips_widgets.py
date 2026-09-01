"""getFinancialLifeKnowledgeArticles 응답 위젯.

의도별 금융생활지식 콘텐츠 목록. Java ``PlayMcpWidgetFactory`` 대응.
"""

from __future__ import annotations

from app.domain.financial_knowledge import Article, FinancialKnowledgeCategory
from app.widgets.common import (
    Widget,
    WidgetResponse,
    open_url_action,
    response,
    send_user_message_action,
)


def financial_knowledge_list(
    category: FinancialKnowledgeCategory,
    articles: list[Article],
) -> WidgetResponse:
    list_items: list[Widget] = [
        {
            "type": "ListViewItem",
            "children": [
                {
                    "type": "Col",
                    "gap": 2,
                    "align": "start",
                    "padding": {"x": 2, "y": 2},
                    "children": [
                        {
                            "type": "Text",
                            "value": category.widget_title,
                            "size": "lg",
                            "weight": "semibold",
                            "textAlign": "start",
                        },
                        {
                            "type": "Caption",
                            "value": f"금융생활지식 ({category.display_name})",
                            "textAlign": "start",
                        },
                    ],
                }
            ],
        }
    ]
    for index, article in enumerate(articles, start=1):
        list_items.append(_financial_knowledge_article_row(index, article))

    next_category = category.next()
    list_items.append(
        {
            "type": "ListViewItem",
            "children": [
                {
                    "type": "Button",
                    "label": "다른 카테고리 보기",
                    "variant": "outline",
                    "block": True,
                    "onClickAction": send_user_message_action(
                        f"{next_category.display_name} 금융생활지식 보여줘"
                    ),
                }
            ],
        }
    )

    widget = {"type": "ListView", "limit": 10, "children": list_items}

    lines = [f"### 금융생활지식 · {category.display_name}", ""]
    for index, article in enumerate(articles, start=1):
        lines.append(f"{index}. [{article.title}]({article.url})")
    copy_text = "\n".join(lines) + "\n"
    return response(widget, copy_text)


def _financial_knowledge_article_row(index: int, article: Article) -> Widget:
    return {
        "type": "ListViewItem",
        "key": article.url,
        "align": "start",
        "gap": 3,
        "onClickAction": open_url_action(article.url),
        "children": [
            {
                "type": "Text",
                "value": f"{index:02d}",
                "weight": "semibold",
                "width": 32,
                "textAlign": "start",
            },
            {
                "type": "Col",
                "flex": 1,
                "align": "start",
                "padding": {"x": 1, "y": 2},
                "children": [
                    {
                        "type": "Text",
                        "value": article.title,
                        "width": "100%",
                        "textAlign": "start",
                        "maxLines": 3,
                    }
                ],
            },
        ],
    }
