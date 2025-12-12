from pydantic import BaseModel, Field

try:
                 
    from pydantic import ConfigDict                
except Exception:                                               
    ConfigDict = None                


                       
class S3BucketInput(BaseModel):
    """Модель даних, яку наш сервіс приймає на вхід для аналізу S3."""

    account_id: str = Field(description="ID хмарного акаунту", example="123456789012")
    bucket_name: str = Field(description="Ім'я S3 бакету", example="my-secure-bucket")
    is_public: bool = Field(description="Чи є бакет публічним")
    encryption_enabled: bool = Field(description="Чи увімкнено шифрування")


                        
class Risk(BaseModel):
    """Модель знайденого ризику, яку сервіс повертає."""

    resource_name: str
    description: str
    severity: str                                      

                                                                                  
    if ConfigDict is not None:
                     
        model_config = ConfigDict(from_attributes=True)                              
    else:
                     
        class Config:                          
            orm_mode = True
