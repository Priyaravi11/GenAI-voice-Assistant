from fastapi import APIRouter, HTTPException

from backend.app.database import billing_collection


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/billing")
async def billing_analytics():
    """
    Return basic analytics from the telecom billing history.
    """

    try:
        total_records = billing_collection.count_documents({})

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_amount": {
                        "$sum": "$amount"
                    },
                    "average_amount": {
                        "$avg": "$amount"
                    },
                }
            }
        ]

        result = list(billing_collection.aggregate(pipeline))

        if result:
            total_amount = result[0].get("total_amount", 0)
            average_amount = result[0].get("average_amount", 0)
        else:
            total_amount = 0
            average_amount = 0

        return {
            "success": True,
            "data": {
                "total_records": total_records,
                "total_amount": total_amount,
                "average_amount": average_amount,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve billing analytics.",
        ) from exc